"""
Bộ thu thập dữ liệu (Crawler Pipeline) cho `kinhthanh.httlvn.org` (`sources/kinhthanh_httlvn/crawler.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/kinhthanh-httlvn.md` (Mục 6: Quy trình Pipeline 4 Bước & Quản lý Trạng thái)
- `crawl_factory/sources/docs/technical-design-and-anti-blocking.md`
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional

from crawl_factory.core.http_client import PoliteHttpClient
from crawl_factory.core.state_manager import StateManager, atomic_write_json, atomic_write_text
from crawl_factory.core.usfm_books import BIBLE_BOOKS_66, BY_USFM, resolve_book
from crawl_factory.sources.kinhthanh_httlvn.parser import parse_httlvn_chapter_html


class KinhthanhHttlvnCrawler:
    """
    Quản lý vòng đời thu thập và phân tích 1.189 chương Kinh Thánh `VI1934` từ `kinhthanh.httlvn.org`.
    """

    SOURCE_ID = "kinhthanh_httlvn"

    def __init__(self, base_dir: Path, config: Dict[str, Any]):
        self.base_dir = base_dir
        self.src_cfg = config["sources"][self.SOURCE_ID]
        self.bible_version = self.src_cfg.get("bible_version", "VI1934")
        self.raw_dir = base_dir / config["paths"]["raw_dir"] / self.SOURCE_ID / self.bible_version
        self.norm_dir = base_dir / config["paths"]["normalized_dir"] / self.SOURCE_ID / self.bible_version
        self.state_file = base_dir / config["paths"]["state_dir"] / f"{self.SOURCE_ID}_state.json"

        self.state = StateManager(self.state_file, self.SOURCE_ID)
        self.client = PoliteHttpClient(
            default_headers=config.get("default_headers"),
            cookies=self.src_cfg.get("cookies"),
            delay_seconds=self.src_cfg.get("delay_seconds", 1.2),
            jitter_seconds=self.src_cfg.get("jitter_seconds", 0.3),
            timeout_seconds=self.src_cfg.get("timeout_seconds", 25),
            max_retries=self.src_cfg.get("max_retries", 4),
        )

    def step_1_init_queue(self) -> Dict[str, int]:
        """
        Bước 1 (Discovery / Queue Init):
        Khởi tạo danh sách 1.189 chương chuẩn từ `BIBLE_BOOKS_66` vào `state/kinhthanh_httlvn_state.json`.
        Bảo toàn trạng thái của những chương đã tải (`fetched` / `parsed`) khi chạy lại.
        """
        items = self.state.data.setdefault("items", {})
        for book in BIBLE_BOOKS_66:
            for ch in range(1, book.chapters + 1):
                key = f"{book.usfm}.{ch}"
                rel_raw = f"{book.httlvn_code}/{ch}.html"
                raw_path = self.raw_dir / rel_raw
                existing = items.get(key, {})
                status = existing.get("status", "pending")
                if status == "pending" and raw_path.exists() and raw_path.stat().st_size > 1024:
                    status = "fetched"

                items[key] = {
                    "usfm": book.usfm,
                    "book_nr": book.book_nr,
                    "httlvn_code": book.httlvn_code,
                    "chapter": ch,
                    "url": book.httlvn_chapter_url(ch, self.bible_version),
                    "raw_rel_path": rel_raw,
                    "status": status,
                    "verse_count": existing.get("verse_count"),
                    "audio_url": existing.get("audio_url"),
                }

        stats = self.state.recompute_stats()
        self.state.save()
        print(f"[{self.SOURCE_ID}:Step1] Đã khởi tạo hàng đợi 1.189 chương. Thống kê: {stats}")
        return stats

    def step_2_fetch_raw(
        self,
        limit: Optional[int] = None,
        filter_book: Optional[str] = None,
        filter_chapter: Optional[int] = None,
        force: bool = False,
    ) -> int:
        """
        Bước 2 (Fetch Raw HTML):
        Tải các chương có `status == 'pending'` (hoặc `'failed'`), kiểm tra chữ ký DOM `bible-read`
        và ghi nguyên tử vào `raw/kinhthanh_httlvn/VI1934/{httlvn_code}/{chapter}.html`.
        """
        if not self.state.data.get("items"):
            self.step_1_init_queue()

        target_book = resolve_book(filter_book) if filter_book else None
        fetched_now = 0
        self.state.install_signal_handler()
        try:
            for key, item in self.state.data["items"].items():
                if self.state.stop_requested:
                    break
                if target_book and item["usfm"] != target_book.usfm:
                    continue
                if filter_chapter is not None and item["chapter"] != filter_chapter:
                    continue

                raw_file = self.raw_dir / item["raw_rel_path"]
                if not force and item.get("status") in ("fetched", "parsed") and raw_file.exists():
                    continue

                url = item["url"]
                print(f"[{self.SOURCE_ID}:Step2] Đang tải {key} ({url})...")
                resp = self.client.request(
                    url,
                    expected_signatures=self.src_cfg.get("expected_signatures", ["bible-read"]),
                )
                atomic_write_text(raw_file, resp.text("utf-8"))
                self.state.update_item(key, {"status": "fetched"}, auto_save=True)
                fetched_now += 1

                if limit is not None and fetched_now >= limit:
                    print(f"[{self.SOURCE_ID}:Step2] Đã đạt giới hạn --limit {limit} chương.")
                    break
        finally:
            self.state.restore_signal_handler()

        print(f"[{self.SOURCE_ID}:Step2] Hoàn tất tải mới {fetched_now} chương. Thống kê: {self.state.recompute_stats()}")
        return fetched_now

    def step_3_parse_normalized(
        self,
        limit: Optional[int] = None,
        filter_book: Optional[str] = None,
        filter_chapter: Optional[int] = None,
    ) -> int:
        """
        Bước 3 (Parse & Normalize):
        Đọc các file HTML đã có trong `raw/`, chạy `parse_httlvn_chapter_html()` xử lý 6 bẫy runtime,
        và xuất JSON chuẩn hóa vào `normalized/kinhthanh_httlvn/VI1934/{USFM}/{chapter}.json`.
        """
        if not self.state.data.get("items"):
            self.step_1_init_queue()

        target_book = resolve_book(filter_book) if filter_book else None
        parsed_now = 0
        for key, item in self.state.data["items"].items():
            if target_book and item["usfm"] != target_book.usfm:
                continue
            if filter_chapter is not None and item["chapter"] != filter_chapter:
                continue

            raw_file = self.raw_dir / item["raw_rel_path"]
            if not raw_file.exists():
                continue

            html_text = raw_file.read_text(encoding="utf-8")
            parsed = parse_httlvn_chapter_html(
                html_text=html_text,
                usfm_book=item["usfm"],
                chapter_num=item["chapter"],
                base_url=self.src_cfg["base_url"],
            )
            out_file = self.norm_dir / item["usfm"] / f"{item['chapter']}.json"
            atomic_write_json(out_file, parsed)

            self.state.update_item(
                key,
                {
                    "status": "parsed",
                    "verse_count": parsed["verse_count"],
                    "audio_url": parsed["audio_url"],
                    "norm_rel_path": f"{item['usfm']}/{item['chapter']}.json",
                },
                auto_save=False,
            )
            parsed_now += 1
            if limit is not None and parsed_now >= limit:
                break

        self.state.save()
        print(f"[{self.SOURCE_ID}:Step3] Đã phân tích cú pháp {parsed_now} chương. Thống kê: {self.state.recompute_stats()}")
        return parsed_now

