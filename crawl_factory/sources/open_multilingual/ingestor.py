"""
Bộ tiếp nhận dữ liệu mở đa ngôn ngữ (`sources/open_multilingual/ingestor.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/multilingual-open-bibles-hymns.md`
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import json

from crawl_factory.core.http_client import PoliteHttpClient
from crawl_factory.core.state_manager import StateManager, atomic_write_json, atomic_write_text
from crawl_factory.core.usfm_books import BIBLE_BOOKS_66, BookSpec, resolve_book
from crawl_factory.sources.open_multilingual.parsers import (
    parse_bolls_jpkjv_chapter,
    parse_morphgnt_chapter_lines,
    parse_wlc_xml_chapter,
)


class OpenMultilingualIngestor:
    """
    Quản lý tải và chuẩn hóa các bản Kinh Thánh đa ngôn ngữ mở (`JA_KOUGO`, `JA_BUNGO`,
    `ORIG_WLC`, `ORIG_GNT`) và Thánh Ca Nhật (`JA_SANBIKA`).
    """

    SOURCE_ID = "open_multilingual"

    def __init__(self, base_dir: Path, config: Dict[str, Any]):
        self.base_dir = base_dir
        self.src_cfg = config["sources"][self.SOURCE_ID]
        self.endpoints = self.src_cfg["endpoints"]
        self.raw_dir = base_dir / config["paths"]["raw_dir"] / self.SOURCE_ID
        self.norm_dir = base_dir / config["paths"]["normalized_dir"] / self.SOURCE_ID
        self.state_file = base_dir / config["paths"]["state_dir"] / f"{self.SOURCE_ID}_state.json"

        self.state = StateManager(self.state_file, self.SOURCE_ID)
        self.client = PoliteHttpClient(
            default_headers=config.get("default_headers"),
            delay_seconds=self.src_cfg.get("delay_seconds", 0.5),
            jitter_seconds=self.src_cfg.get("jitter_seconds", 0.2),
            timeout_seconds=self.src_cfg.get("timeout_seconds", 45),
            max_retries=self.src_cfg.get("max_retries", 3),
        )

    def ingest_chapter_multilang(self, book: BookSpec, chapter: int, force: bool = False) -> Dict[str, Any]:
        """
        Tải và phân tích đồng bộ 1 chương cho:
        - `JA_KOUGO` (Bolls.life JPKJV kèm Ruby Furigana, xử lý TRAP B1 `[0]`/`[00]`)
        - `JA_BUNGO` (GetBible japbungo)
        - `ORIG_WLC` (nếu là Cựu Ước, xử lý TRAP C2 `lemma` + `/`) hoặc `ORIG_GNT` (nếu là Tân Ước, xử lý TRAP C3)
        """
        key = f"{book.usfm}.{chapter}"

        # 1. JA_KOUGO (Bolls.life JPKJV chapter endpoint)
        bolls_raw_file = self.raw_dir / "ja_kougo_bolls" / book.usfm / f"{chapter}.json"
        if force or not bolls_raw_file.exists():
            url_bolls = self.endpoints["ja_kougo_bolls_chapter_tpl"].format(
                book_nr=book.book_nr, chapter=chapter
            )
            print(f"[{self.SOURCE_ID}] Đang tải JA_KOUGO (Bolls Ruby) cho {key}: {url_bolls}...")
            resp = self.client.request(url_bolls)
            atomic_write_text(bolls_raw_file, resp.text("utf-8"))

        raw_bolls_list = json.loads(bolls_raw_file.read_text(encoding="utf-8"))
        parsed_kougo = parse_bolls_jpkjv_chapter(raw_bolls_list, book.usfm, chapter)
        atomic_write_json(self.norm_dir / "ja_kougo" / book.usfm / f"{chapter}.json", parsed_kougo)

        # 2. JA_BUNGO (GetBible japbungo chapter endpoint)
        bungo_raw_file = self.raw_dir / "ja_bungo" / book.usfm / f"{chapter}.json"
        if force or not bungo_raw_file.exists():
            url_bungo = self.endpoints["ja_bungo_getbible_chapter_tpl"].format(
                book_nr=book.book_nr, chapter=chapter
            )
            print(f"[{self.SOURCE_ID}] Đang tải JA_BUNGO cho {key}: {url_bungo}...")
            resp = self.client.request(url_bungo)
            atomic_write_text(bungo_raw_file, resp.text("utf-8"))

        bungo_json = json.loads(bungo_raw_file.read_text(encoding="utf-8"))
        parsed_bungo = {
            "version": "JA_BUNGO",
            "usfm": book.usfm,
            "chapter": chapter,
            "verse_count": len(bungo_json.get("verses", [])),
            "verses": [
                {
                    "verse_id": f"{book.usfm}.{chapter}.{int(v['verse'])}",
                    "verse": int(v["verse"]),
                    "text": (v.get("text") or "").strip(),
                }
                for v in bungo_json.get("verses", [])
            ],
        }
        atomic_write_json(self.norm_dir / "ja_bungo" / book.usfm / f"{chapter}.json", parsed_bungo)

        # 3. Ngôn ngữ gốc: ORIG_WLC (Cựu Ước) hoặc ORIG_GNT (Tân Ước)
        orig_count = 0
        if book.testament == "OT" and book.wlc_osis:
            wlc_book_file = self.raw_dir / "orig_wlc" / f"{book.wlc_osis}.xml"
            if force or not wlc_book_file.exists():
                url_wlc = self.endpoints["orig_wlc_book_tpl"].format(wlc_osis=book.wlc_osis)
                print(f"[{self.SOURCE_ID}] Đang tải sách Cựu Ước Hê-bơ-rơ WLC ({book.wlc_osis}.xml)...")
                resp = self.client.request(url_wlc)
                atomic_write_text(wlc_book_file, resp.text("utf-8"))

            parsed_wlc = parse_wlc_xml_chapter(
                wlc_book_file.read_text(encoding="utf-8"),
                book.wlc_osis,
                chapter,
                book.usfm,
            )
            atomic_write_json(self.norm_dir / "orig_wlc" / book.usfm / f"{chapter}.json", parsed_wlc)
            orig_count = parsed_wlc["verse_count"]

        elif book.testament == "NT" and book.morphgnt_prefix:
            gnt_book_file = self.raw_dir / "orig_gnt" / f"{book.morphgnt_prefix}-morphgnt.txt"
            if force or not gnt_book_file.exists():
                url_gnt = self.endpoints["orig_gnt_book_tpl"].format(morphgnt_prefix=book.morphgnt_prefix)
                print(f"[{self.SOURCE_ID}] Đang tải sách Tân Ước Hy Lạp MorphGNT ({book.morphgnt_prefix})...")
                resp = self.client.request(url_gnt)
                atomic_write_text(gnt_book_file, resp.text("utf-8"))

            nt_idx = book.book_nr - 39  # MAT=40 -> 01
            parsed_gnt = parse_morphgnt_chapter_lines(
                gnt_book_file.read_text(encoding="utf-8"),
                nt_idx,
                chapter,
                book.usfm,
            )
            atomic_write_json(self.norm_dir / "orig_gnt" / book.usfm / f"{chapter}.json", parsed_gnt)
            orig_count = parsed_gnt["verse_count"]

        info = {
            "status": "parsed",
            "ja_kougo_verses": parsed_kougo["verse_count"],
            "ja_bungo_verses": parsed_bungo["verse_count"],
            "orig_verses": orig_count,
        }
        self.state.update_item(key, info, auto_save=True)
        return info

    def run_pipeline(
        self,
        limit: Optional[int] = None,
        filter_book: Optional[str] = None,
        filter_chapter: Optional[int] = None,
        include_sanbika: bool = True,
        force: bool = False,
    ) -> int:
        """Chạy thu thập & chuẩn hóa đa ngôn ngữ theo giới hạn `--limit`."""
        target_book = resolve_book(filter_book) if filter_book else None
        processed = 0
        self.state.install_signal_handler()
        try:
            for book in BIBLE_BOOKS_66:
                if target_book and book.usfm != target_book.usfm:
                    continue
                for ch in range(1, book.chapters + 1):
                    if self.state.stop_requested:
                        break
                    if filter_chapter is not None and ch != filter_chapter:
                        continue
                    key = f"{book.usfm}.{ch}"
                    existing = self.state.get_item(key)
                    if not force and existing and existing.get("status") == "parsed":
                        continue

                    self.ingest_chapter_multilang(book, ch, force=force)
                    processed += 1
                    if limit is not None and processed >= limit:
                        break
                if self.state.stop_requested or (limit is not None and processed >= limit):
                    break

            if include_sanbika and not self.state.stop_requested:
                sanbika_raw = self.raw_dir / "sanbika" / "kanichi_songs.json"
                if force or not sanbika_raw.exists():
                    url_sb = self.endpoints["sanbika_kanichi_json"]
                    print(f"[{self.SOURCE_ID}] Đang tải dữ liệu Thánh Ca Nhật Sanbika từ {url_sb}...")
                    resp = self.client.request(url_sb)
                    atomic_write_text(sanbika_raw, resp.text("utf-8"))
                songs = json.loads(sanbika_raw.read_text(encoding="utf-8"))
                atomic_write_json(self.norm_dir / "ja_sanbika" / "songs.json", songs)
                self.state.update_item("SANBIKA_JSON", {"status": "parsed", "song_count": len(songs)}, auto_save=True)
        finally:
            self.state.restore_signal_handler()

        print(f"[{self.SOURCE_ID}] Hoàn tất xử lý {processed} chương đa ngữ.")
        return processed

