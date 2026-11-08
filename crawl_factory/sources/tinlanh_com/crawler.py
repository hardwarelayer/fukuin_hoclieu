"""
Bộ thu thập & kiểm định 3 nguồn (Crawler + 3-Way Oracle) cho `www.tinlanh.com` và `GetBible vietnamese`.

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/tinlanh-com.md` (Mục 3 & 4)
- `crawl_factory/sources/docs/technical-design-and-anti-blocking.md` (TRAP F3 & F4)

Tối ưu hóa chống giới hạn số trang / băng thông (Quota & Rate Protection):
1. Tải trọn gói 66 sách `GetBible vietnamese.json` (`2.07 MB` nén gzip) chỉ bằng **1 HTTP Request duy nhất**
   vào `raw/getbible_vietnamese/vietnamese_full.json` (tiết kiệm 1.188 requests!).
2. Chế độ **Smart Tie-Breaker (Mặc định)**:
   - So khớp cục bộ từng câu của `kinhthanh_httlvn` với `vietnamese_full.json` (`0` request mạng).
   - Ở `> 95%` số chương nơi `kinhthanh_httlvn` và `GetBible` đã khớp 100% (2/3 Majority đạt được ngay lập tức),
     không cần gọi lên `www.tinlanh.com` (tránh hoàn toàn giới hạn cửa sổ trượt của Hostinger LiteSpeed!).
   - Chỉ gọi `GET .shtml` lên `www.tinlanh.com` cho những chương có câu khác biệt giữa `kinhthanh_httlvn` và `GetBible`
     (hoặc khi truyền cờ `--force` / lọc `--book` cụ thể).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from crawl_factory.core.http_client import PoliteHttpClient, ProxyRotator
from crawl_factory.core.state_manager import StateManager, atomic_write_json, atomic_write_text
from crawl_factory.core.text_normalizer import normalize_vietnamese_1925
from crawl_factory.core.usfm_books import BIBLE_BOOKS_66, resolve_book
from crawl_factory.sources.tinlanh_com.parser import (
    _strip_punctuation_for_vote,
    parse_tinlanh_shtml,
    resolve_verse_3way,
)


class TinlanhComCrawler:
    """
    Quản lý thu thập `.shtml` từ `www.tinlanh.com`, tải gói Bulk `GetBible vietnamese.json` (1 request = 2.07 MB gzip),
    và chạy thuật toán Biểu quyết Đa số 2/3 (3-Way Majority Voting) với `kinhthanh_httlvn`.
    """

    SOURCE_ID = "tinlanh_com"

    def __init__(self, base_dir: Path, config: Dict[str, Any], proxy_rotator: Optional[ProxyRotator] = None):
        self.base_dir = base_dir
        self.src_cfg = config["sources"][self.SOURCE_ID]
        self.raw_dir = base_dir / config["paths"]["raw_dir"] / self.SOURCE_ID
        self.getbible_raw_dir = base_dir / config["paths"]["raw_dir"] / "getbible_vietnamese"
        self.getbible_bulk_file = self.getbible_raw_dir / "vietnamese_full.json"
        self.norm_dir = base_dir / config["paths"]["normalized_dir"] / self.SOURCE_ID
        self.httlvn_norm_dir = (
            base_dir / config["paths"]["normalized_dir"] / "kinhthanh_httlvn" / "VI1934"
        )
        self.state_file = base_dir / config["paths"]["state_dir"] / f"{self.SOURCE_ID}_state.json"
        self.report_file = base_dir / config["paths"]["state_dir"] / "bible_1925_verification_report.json"

        self.state = StateManager(self.state_file, self.SOURCE_ID)
        self.client = PoliteHttpClient(
            default_headers=config.get("default_headers"),
            delay_seconds=self.src_cfg.get("delay_seconds", 0.6),
            jitter_seconds=self.src_cfg.get("jitter_seconds", 0.2),
            timeout_seconds=self.src_cfg.get("timeout_seconds", 20),
            max_retries=self.src_cfg.get("max_retries", 3),
            batch_size=self.src_cfg.get("batch_size", 80),
            batch_pause_seconds=self.src_cfg.get("batch_pause_seconds", 30.0),
            proxy_rotator=proxy_rotator,
        )
        self._getbible_bulk_index: Optional[Dict[str, Dict[int, str]]] = None

    def ensure_getbible_bulk_loaded(self, force: bool = False) -> Dict[str, Dict[int, str]]:
        """
        Tải gói nguyên khối `https://api.getbible.net/v2/vietnamese.json` (chỉ 1 HTTP request, 2.07 MB gzip)
        và lập chỉ mục O(1) `{"PSA.23": {1: "Đức Giê-hô-va...", ...}}` trong bộ nhớ.
        """
        if self._getbible_bulk_index is not None and not force:
            return self._getbible_bulk_index

        if force or not self.getbible_bulk_file.exists():
            bulk_url = self.src_cfg.get("getbible_vi_url", "https://api.getbible.net/v2/vietnamese.json")
            print(f"[{self.SOURCE_ID}] Tải trọn bộ 66 sách GetBible (1 request = 2.07 MB gzip) từ {bulk_url}...")
            resp = self.client.request(bulk_url)
            atomic_write_text(self.getbible_bulk_file, resp.text("utf-8"))

        raw_data = json.loads(self.getbible_bulk_file.read_text(encoding="utf-8"))
        nr_to_usfm = {b.book_nr: b.usfm for b in BIBLE_BOOKS_66}
        index: Dict[str, Dict[int, str]] = {}

        for book_obj in raw_data.get("books", []):
            b_nr = int(book_obj.get("nr", 0))
            usfm = nr_to_usfm.get(b_nr)
            if not usfm:
                continue
            for ch_obj in book_obj.get("chapters", []):
                ch_num = int(ch_obj.get("chapter", 0))
                ch_key = f"{usfm}.{ch_num}"
                v_map: Dict[int, str] = {}
                for v_obj in ch_obj.get("verses", []):
                    v_num = int(v_obj["verse"])
                    # Sửa TRAP B2: Ð (U+00D0) -> Đ (U+0110)
                    v_map[v_num] = normalize_vietnamese_1925(v_obj.get("text", ""), preserve_newlines=False)
                index[ch_key] = v_map

        self._getbible_bulk_index = index
        return index

    def _chapter_needs_tinlanh_tiebreaker(self, ch_key: str, gb_verses: Dict[int, str]) -> bool:
        """
        Kiểm tra xem chương `ch_key` giữa `kinhthanh_httlvn` và `GetBible` có bất kỳ câu nào
        lệch từ vựng hay không. Nếu khớp 100% (2/3 Majority đã đạt), không cần tốn request vào `tinlanh.com`.
        """
        usfm, ch_str = ch_key.split(".")
        httlvn_file = self.httlvn_norm_dir / usfm / f"{ch_str}.json"
        if not httlvn_file.exists():
            return True
        httlvn_doc = json.loads(httlvn_file.read_text(encoding="utf-8"))
        for v_obj in httlvn_doc.get("verses", []):
            if v_obj.get("is_omitted_in_critical_text"):
                continue
            v_num = int(v_obj["verse"])
            a = _strip_punctuation_for_vote(v_obj.get("text", ""))
            c = _strip_punctuation_for_vote(gb_verses.get(v_num, ""))
            if a != c:
                return True
        return False

    def step_1_init_queue(self) -> Dict[str, int]:
        """Khởi tạo hàng đợi 1.189 chương `.shtml` trên `www.tinlanh.com`."""
        items = self.state.data.setdefault("items", {})
        for book in BIBLE_BOOKS_66:
            for ch in range(1, book.chapters + 1):
                key = f"{book.usfm}.{ch}"
                rel_raw = f"{book.tinlanh_testament_dir}/{book.tinlanh_slug}/{book.tinlanh_slug}{ch}.shtml"
                raw_path = self.raw_dir / rel_raw
                existing = items.get(key, {})
                status = existing.get("status", "pending")
                if status == "pending" and raw_path.exists() and raw_path.stat().st_size > 256:
                    status = "fetched"

                items[key] = {
                    "usfm": book.usfm,
                    "book_nr": book.book_nr,
                    "tinlanh_slug": book.tinlanh_slug,
                    "chapter": ch,
                    "url": book.tinlanh_chapter_url(ch),
                    "raw_rel_path": rel_raw,
                    "status": status,
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
        smart_tiebreaker_only: bool = True,
        force: bool = False,
    ) -> int:
        """
        Tải gói Bulk `GetBible vietnamese.json` (1 request) và tải `.shtml` từ `www.tinlanh.com`
        (chỉ tải khi cần phân xử 3 bên hoặc khi truyền `--book` / `--force`).
        """
        if not self.state.data.get("items"):
            self.step_1_init_queue()

        gb_index = self.ensure_getbible_bulk_loaded(force=force)
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

                # Nếu chạy toàn cục (không ép --book cụ thể) và bật smart_tiebreaker_only,
                # bỏ qua gọi tinlanh.com nếu HTTLVN và GetBible đã khớp 100%!
                if (
                    smart_tiebreaker_only
                    and not force
                    and target_book is None
                    and not self._chapter_needs_tinlanh_tiebreaker(key, gb_index.get(key, {}))
                ):
                    self.state.update_item(key, {"status": "skipped_unanimous_2way"}, auto_save=False)
                    continue

                print(f"[{self.SOURCE_ID}:Step2] Đang tải Tie-Breaker {key} từ tinlanh.com ({item['url']})...")
                resp = self.client.request(
                    item["url"],
                    expected_signatures=self.src_cfg.get("expected_signatures", ['class="bread"']),
                )
                atomic_write_text(raw_file, resp.text("utf-8"))
                self.state.update_item(key, {"status": "fetched"}, auto_save=True)
                fetched_now += 1
                if limit is not None and fetched_now >= limit:
                    print(f"[{self.SOURCE_ID}:Step2] Đã đạt giới hạn --limit {limit} chương.")
                    break
        finally:
            self.state.restore_signal_handler()
            self.state.save()

        print(f"[{self.SOURCE_ID}:Step2] Hoàn tất tải mới {fetched_now} chương `.shtml`.")
        return fetched_now

    def step_3_parse_and_verify_3way(
        self,
        limit: Optional[int] = None,
        filter_book: Optional[str] = None,
        filter_chapter: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Bước 3: Đối chiếu 3 nguồn (`kinhthanh_httlvn` vs `GetBible Bulk` vs `tinlanh.com .shtml`).
        """
        if not self.state.data.get("items"):
            self.step_1_init_queue()

        gb_index = self.ensure_getbible_bulk_loaded(force=False)
        target_book = resolve_book(filter_book) if filter_book else None
        vote_counts: Dict[str, int] = {}
        discrepancies: List[Dict[str, Any]] = []
        chapters_verified = 0

        for key, item in self.state.data["items"].items():
            if target_book and item["usfm"] != target_book.usfm:
                continue
            if filter_chapter is not None and item["chapter"] != filter_chapter:
                continue

            httlvn_file = self.httlvn_norm_dir / item["usfm"] / f"{item['chapter']}.json"
            raw_file = self.raw_dir / item["raw_rel_path"]
            if not httlvn_file.exists() and not raw_file.exists():
                continue

            tl_map: Dict[int, str] = {}
            if raw_file.exists():
                parsed_tl = parse_tinlanh_shtml(
                    raw_file.read_text(encoding="utf-8"),
                    item["usfm"],
                    item["chapter"],
                )
                tl_map = {v["verse"]: v["text"] for v in parsed_tl["verses"]}

            gb_map = gb_index.get(key, {})

            httlvn_map: Dict[int, str] = {}
            if httlvn_file.exists():
                httlvn_json = json.loads(httlvn_file.read_text(encoding="utf-8"))
                for v_obj in httlvn_json.get("verses", []):
                    httlvn_map[int(v_obj["verse"])] = v_obj.get("text", "")

            all_v_nums = sorted(set(tl_map.keys()) | set(gb_map.keys()) | set(httlvn_map.keys()))
            verified_verses = []
            for v_num in all_v_nums:
                vid = f"{item['usfm']}.{item['chapter']}.{v_num}"
                res = resolve_verse_3way(
                    httlvn_map.get(v_num),
                    tl_map.get(v_num),
                    gb_map.get(v_num),
                    vid,
                )
                st = res["status"]
                vote_counts[st] = vote_counts.get(st, 0) + 1
                if res["discrepancy"]:
                    discrepancies.append(res["discrepancy"])
                verified_verses.append({
                    "verse_id": vid,
                    "verse": v_num,
                    "vote_status": st,
                    "chosen_text": res["chosen_text"],
                    "tinlanh_text": tl_map.get(v_num),
                    "getbible_text": gb_map.get(v_num),
                })

            out_file = self.norm_dir / item["usfm"] / f"{item['chapter']}.json"
            atomic_write_json(
                out_file,
                {
                    "chapter_id": key,
                    "usfm": item["usfm"],
                    "chapter": item["chapter"],
                    "verse_count": len(verified_verses),
                    "verses": verified_verses,
                },
            )
            self.state.update_item(key, {"status": "parsed", "verse_count": len(verified_verses)}, auto_save=False)
            chapters_verified += 1
            if limit is not None and chapters_verified >= limit:
                break

        self.state.save()
        report = {
            "chapters_verified": chapters_verified,
            "vote_summary": vote_counts,
            "discrepancy_count": len(discrepancies),
            "discrepancies": discrepancies[:200],
        }
        atomic_write_json(self.report_file, report)
        print(
            f"[{self.SOURCE_ID}:Step3] Đã đối chiếu 3 nguồn cho {chapters_verified} chương. "
            f"Kết quả bỏ phiếu: {vote_counts}"
        )
        return report
