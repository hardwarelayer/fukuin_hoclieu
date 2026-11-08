"""
Quản lý trạng thái tiến độ (`state/*.json`) và ghi file nguyên tử (`state_manager.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/technical-design-and-anti-blocking.md` (Mục 2.1: Atomic Write & Ctrl+C)

Nguyên tắc thiết kế cho team phát triển:
1. Mọi file trong `state/` và `raw/` đều phải được ghi qua hàm `atomic_write_*`
   (ghi ra file tạm `*.tmp`, gọi `os.fsync`, sau đó `os.replace`) để đảm bảo không bao giờ
   sinh ra file JSON/HTML bị cắt cụt (corrupted) khi mất điện hoặc nhấn `Ctrl+C`.
2. Lớp `StateManager` tự động bắt tín hiệu `SIGINT` (`Ctrl+C`): khi người vận hành nhấn
   `Ctrl+C` một lần, cờ `state.stop_requested` bật lên `True`, vòng lặp crawl sẽ hoàn tất
   nốt item đang xử lý, lưu checkpoint vào `state/{source}_state.json` và thoát êm ái.
"""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os
import signal


def utc_now_iso() -> str:
    """Trả về chuỗi thời gian UTC chuẩn ISO-8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write_bytes(target_path: Path | str, data: bytes) -> None:
    """Ghi mảng byte nguyên tử vào đĩa qua file `.tmp` + `os.replace`."""
    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = p.with_suffix(p.suffix + f".{os.getpid()}.tmp")
    with open(tmp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, p)


def atomic_write_text(target_path: Path | str, text: str, encoding: str = "utf-8") -> None:
    """Ghi chuỗi văn bản nguyên tử vào đĩa."""
    atomic_write_bytes(target_path, text.encode(encoding))


def atomic_write_json(target_path: Path | str, obj: Any) -> None:
    """Ghi đối tượng JSON nguyên tử vào đĩa (UTF-8, indent=2)."""
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(target_path, text, encoding="utf-8")


class StateManager:
    """
    Quản lý vòng đời file trạng thái `state/{source_id}_state.json` và bắt tín hiệu `Ctrl+C`.
    """

    def __init__(self, state_file: Path | str, source_id: str, default_payload: Optional[Dict[str, Any]] = None):
        self.state_file = Path(state_file)
        self.source_id = source_id
        self.stop_requested: bool = False
        self._prev_sigint_handler = None

        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                self.data: Dict[str, Any] = json.load(f)
        else:
            self.data = default_payload or {
                "source": source_id,
                "created_at": utc_now_iso(),
                "last_updated": utc_now_iso(),
                "stats": {},
                "items": {},
            }

    def install_signal_handler(self) -> None:
        """Đăng ký bắt `SIGINT` (Ctrl+C) để dừng vòng lặp an toàn sau khi lưu item hiện tại."""
        def _handler(signum, frame):
            if not self.stop_requested:
                print(
                    f"\n[StateManager:{self.source_id}] Đã nhận tín hiệu dừng (Ctrl+C). "
                    f"Đang hoàn tất item hiện tại và lưu checkpoint vào {self.state_file}..."
                )
                self.stop_requested = True
            else:
                print(f"\n[StateManager:{self.source_id}] Nhận Ctrl+C lần 2 — lưu khẩn cấp và thoát!")
                self.save()
                raise KeyboardInterrupt

        self._prev_sigint_handler = signal.signal(signal.SIGINT, _handler)

    def restore_signal_handler(self) -> None:
        """Khôi phục signal handler ban đầu sau khi kết thúc bước chạy."""
        if self._prev_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._prev_sigint_handler)
            self._prev_sigint_handler = None

    def save(self) -> None:
        """Lưu nguyên tử trạng thái hiện tại ra `self.state_file`."""
        self.data["last_updated"] = utc_now_iso()
        atomic_write_json(self.state_file, self.data)

    def get_item(self, item_key: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin trạng thái của 1 item (ví dụ `'GEN.1'` hoặc `'hymn_1'`)."""
        return self.data.setdefault("items", {}).get(item_key)

    def update_item(self, item_key: str, fields: Dict[str, Any], auto_save: bool = True) -> Dict[str, Any]:
        """Cập nhật trạng thái của 1 item và tùy chọn lưu ngay checkpoint."""
        items = self.data.setdefault("items", {})
        entry = items.setdefault(item_key, {})
        entry.update(fields)
        entry["updated_at"] = utc_now_iso()
        self.recompute_stats()
        if auto_save:
            self.save()
        return entry

    def recompute_stats(self) -> Dict[str, int]:
        """Tính lại bảng thống kê tổng hợp `stats` từ danh sách `items`."""
        items = self.data.get("items", {})
        counts: Dict[str, int] = {"total": len(items)}
        for info in items.values():
            st = info.get("status", "pending")
            counts[st] = counts.get(st, 0) + 1
        self.data["stats"] = counts
        return counts

