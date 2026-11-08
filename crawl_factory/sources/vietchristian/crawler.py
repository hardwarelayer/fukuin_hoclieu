"""
Bộ thu thập dữ liệu tĩnh (7-Request Static Fetcher) cho `vietchristian.com` (`sources/vietchristian/crawler.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/vietchristian.md` (Mục 1.2 & Mục 4)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional

from crawl_factory.core.http_client import PoliteHttpClient
from crawl_factory.core.state_manager import StateManager, atomic_write_json, atomic_write_text
from crawl_factory.core.text_normalizer import normalize_vietnamese_1925
from crawl_factory.sources.vietchristian.parser import (
    parse_duong_linh_topics,
    parse_hymn_index_result_asp,
    parse_tklk_xml,
)


class VietchristianCrawler:
    """
    Quản lý tải 7 tài nguyên tĩnh/mục lục trên `vietchristian.com` với delay an toàn 2.5s
    để tránh hoàn toàn Cloudflare `jsd` challenge.
    """

    SOURCE_ID = "vietchristian"

    STATIC_TASKS = [
        ("tklk_xml", "GET", "/kinhthanh/tklk/tklk.xml", None, "tklk.xml"),
        ("kinhthanh_home", "GET", "/kinhthanh/", None, "kinhthanh_home.html"),
        ("events_calendar", "GET", "/event/", None, "events.html"),
        ("ktdd_txt", "GET", "/thanhca/ktdd.txt", None, "ktdd.txt"),
        ("thanhca_txt", "GET", "/thanhca/thanhca.txt", None, "thanhca.txt"),
        ("hymn_index_hid0", "POST", "/thanhca/result.asp", {"vn": "1", "Searchtype": "index", "hid": "0"}, "hymn_index_hid0.html"),
        ("hymn_index_hid1", "POST", "/thanhca/result.asp", {"vn": "1", "Searchtype": "index", "hid": "1"}, "hymn_index_hid1.html"),
    ]

    def __init__(self, base_dir: Path, config: Dict[str, Any]):
        self.base_dir = base_dir
        self.src_cfg = config["sources"][self.SOURCE_ID]
        self.base_url = self.src_cfg["base_url"].rstrip("/")
        self.raw_dir = base_dir / config["paths"]["raw_dir"] / self.SOURCE_ID
        self.norm_dir = base_dir / config["paths"]["normalized_dir"] / self.SOURCE_ID
        self.state_file = base_dir / config["paths"]["state_dir"] / f"{self.SOURCE_ID}_state.json"

        self.state = StateManager(self.state_file, self.SOURCE_ID)
        self.client = PoliteHttpClient(
            default_headers=config.get("default_headers"),
            delay_seconds=self.src_cfg.get("delay_seconds", 2.5),
            jitter_seconds=self.src_cfg.get("jitter_seconds", 0.5),
            timeout_seconds=self.src_cfg.get("timeout_seconds", 25),
            max_retries=self.src_cfg.get("max_retries", 3),
        )

    def step_1_init_queue(self) -> Dict[str, int]:
        items = self.state.data.setdefault("items", {})
        for key, method, path, form_data, filename in self.STATIC_TASKS:
            raw_path = self.raw_dir / filename
            existing = items.get(key, {})
            status = existing.get("status", "pending")
            if status == "pending" and raw_path.exists() and raw_path.stat().st_size > 128:
                status = "fetched"
            items[key] = {
                "method": method,
                "url": f"{self.base_url}{path}",
                "form_data": form_data,
                "raw_rel_path": filename,
                "status": status,
            }
        stats = self.state.recompute_stats()
        self.state.save()
        print(f"[{self.SOURCE_ID}:Step1] Đã khởi tạo 7 tác vụ tĩnh. Thống kê: {stats}")
        return stats

    def step_2_fetch_raw(self, limit: Optional[int] = None, force: bool = False) -> int:
        if not self.state.data.get("items"):
            self.step_1_init_queue()

        fetched_now = 0
        self.state.install_signal_handler()
        try:
            for key, item in self.state.data["items"].items():
                if self.state.stop_requested:
                    break
                raw_file = self.raw_dir / item["raw_rel_path"]
                if not force and item.get("status") in ("fetched", "parsed") and raw_file.exists():
                    continue

                print(f"[{self.SOURCE_ID}:Step2] Đang tải {key} ({item['method']} {item['url']})...")
                resp = self.client.request(
                    item["url"],
                    method=item["method"],
                    form_data=item.get("form_data"),
                )
                atomic_write_text(raw_file, resp.text("utf-8"))
                self.state.update_item(key, {"status": "fetched"}, auto_save=True)
                fetched_now += 1
                if limit is not None and fetched_now >= limit:
                    break
        finally:
            self.state.restore_signal_handler()

        print(f"[{self.SOURCE_ID}:Step2] Hoàn tất tải mới {fetched_now} tệp.")
        return fetched_now

    def step_3_parse_normalized(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        tklk_file = self.raw_dir / "tklk.xml"
        if tklk_file.exists():
            books = parse_tklk_xml(tklk_file.read_text(encoding="utf-8"))
            atomic_write_json(self.norm_dir / "tklk_outline.json", books)
            self.state.update_item("tklk_xml", {"status": "parsed", "book_count": len(books)}, auto_save=False)
            summary["tklk_books"] = len(books)

        home_file = self.raw_dir / "kinhthanh_home.html"
        if home_file.exists():
            topics = parse_duong_linh_topics(home_file.read_text(encoding="utf-8"))
            atomic_write_json(self.norm_dir / "mood_scripture_seeds.json", topics)
            self.state.update_item("kinhthanh_home", {"status": "parsed", "topic_count": len(topics)}, auto_save=False)
            summary["mood_topics"] = len(topics)

        for hid in (0, 1):
            idx_file = self.raw_dir / f"hymn_index_hid{hid}.html"
            if idx_file.exists():
                entries = parse_hymn_index_result_asp(idx_file.read_text(encoding="utf-8"), hymnal_id=hid)
                atomic_write_json(self.norm_dir / f"hymn_index_hid{hid}.json", entries)
                self.state.update_item(f"hymn_index_hid{hid}", {"status": "parsed", "count": len(entries)}, auto_save=False)
                summary[f"hymn_index_hid{hid}"] = len(entries)

        for txt_key, fname in (("ktdd_txt", "ktdd.txt"), ("thanhca_txt", "thanhca.txt")):
            f_path = self.raw_dir / fname
            if f_path.exists():
                cleaned = normalize_vietnamese_1925(f_path.read_text(encoding="utf-8"), preserve_newlines=True)
                atomic_write_text(self.norm_dir / f"clean_{fname}", cleaned)
                self.state.update_item(txt_key, {"status": "parsed", "char_len": len(cleaned)}, auto_save=False)
                summary[txt_key] = len(cleaned)

        self.state.save()
        print(f"[{self.SOURCE_ID}:Step3] Hoàn tất chuẩn hóa dữ liệu vietchristian: {summary}")
        return summary

