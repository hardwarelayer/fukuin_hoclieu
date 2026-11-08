"""
Bộ thu thập dữ liệu (Crawler Pipeline) cho `thanhca.httlvn.org` (`sources/thanhca_httlvn/crawler.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/thanhca-httlvn.md` (Mục 1.2 & Mục 4: Chiến lược giảm 78% request & Pipeline)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

from crawl_factory.core.http_client import PoliteHttpClient
from crawl_factory.core.music_sheet_distiller import distill_musicxml_file
from crawl_factory.core.state_manager import StateManager, atomic_write_bytes, atomic_write_json, atomic_write_text
from crawl_factory.sources.thanhca_httlvn.parser import (
    parse_hymn_chords_html,
    parse_mp3_playlist_html,
    parse_responsive_reading_html,
    parse_responsive_reading_index_html,
)


class ThanhcaHttlvnCrawler:
    """
    Quản lý thu thập 903 bài Thánh Ca Tin Lành (Lời + Hợp âm ChordPro + MusicXML + MP3/YouTube metadata)
    và 100 bài Kinh Thánh Đối Đáp từ `thanhca.httlvn.org`.
    """

    SOURCE_ID = "thanhca_httlvn"

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
            delay_seconds=self.src_cfg.get("delay_seconds", 1.0),
            jitter_seconds=self.src_cfg.get("jitter_seconds", 0.3),
            timeout_seconds=self.src_cfg.get("timeout_seconds", 25),
            max_retries=self.src_cfg.get("max_retries", 4),
        )

    def step_1_init_queue(self, discover_mp3_playlist: bool = True) -> Dict[str, int]:
        """
        Bước 1 (Discovery & Capability Mapping):
        - Khởi tạo 903 bài Thánh Ca (`hymn_1`..`hymn_903`) và 100 bài KTĐĐ (`ktdd_1`..`ktdd_100`).
        - Tải 1 trang `/thanh-ca-1/cui-xin-vua-thanh-ngu-lai?op=mp3` để lấy trọn danh sách 384 bài có MP3
          (TRAP D3 - tiết kiệm 902 requests!) và 1 trang `/kinh-thanh-doi-dap` (khử trùng 200 -> 100 link - TRAP D8).
        """
        mp3_ids: List[int] = self.state.data.get("mp3_available_ids", [])
        if discover_mp3_playlist and not mp3_ids:
            mp3_seed_file = self.raw_dir / "indices" / "hymn_1_mp3_playlist.html"
            if not mp3_seed_file.exists():
                url = f"{self.base_url}/thanh-ca-1/cui-xin-vua-thanh-ngu-lai?op=mp3"
                print(f"[{self.SOURCE_ID}:Step1] Tải playlist 384 bài MP3 từ {url}...")
                resp = self.client.request(url)
                atomic_write_text(mp3_seed_file, resp.text("utf-8"))
            mp3_ids = parse_mp3_playlist_html(mp3_seed_file.read_text(encoding="utf-8"))
            self.state.data["mp3_available_ids"] = mp3_ids

        ktdd_index_file = self.raw_dir / "indices" / "ktdd_index.html"
        if discover_mp3_playlist and not ktdd_index_file.exists():
            url = f"{self.base_url}/kinh-thanh-doi-dap"
            print(f"[{self.SOURCE_ID}:Step1] Tải mục lục 100 bài KTĐĐ từ {url}...")
            resp = self.client.request(url)
            atomic_write_text(ktdd_index_file, resp.text("utf-8"))

        ktdd_meta_map: Dict[int, Dict[str, Any]] = {}
        if ktdd_index_file.exists():
            for row in parse_responsive_reading_index_html(ktdd_index_file.read_text(encoding="utf-8")):
                ktdd_meta_map[row["reading_id"]] = row

        mp3_set = set(mp3_ids)
        items = self.state.data.setdefault("items", {})

        # 1. Khởi tạo 903 bài Thánh Ca
        for hid in range(1, 904):
            key = f"hymn_{hid}"
            existing = items.get(key, {})
            rel_chords = f"chords/{hid}.html"
            raw_path = self.raw_dir / rel_chords
            status = existing.get("status", "pending")
            if status == "pending" and raw_path.exists() and raw_path.stat().st_size > 512:
                status = "fetched"

            items[key] = {
                "item_type": "hymn",
                "hymn_id": hid,
                "slug": existing.get("slug", ""),
                "url_chords": f"{self.base_url}/thanh-ca-{hid}?op=chords",
                "url_musicxml": f"{self.base_url}/Download/SheetMusic/{hid}",
                "has_mp3": hid in mp3_set,
                "mp3_url": f"https://audio.httlvn.org/TC/thanh-ca/mp3/{hid}.mp3" if hid in mp3_set else None,
                "musicxml_status": existing.get("musicxml_status", "pending"),
                "raw_rel_path": rel_chords,
                "status": status,
            }

        # 2. Khởi tạo 100 bài Kinh Thánh Đối Đáp
        for rid in range(1, 101):
            key = f"ktdd_{rid}"
            existing = items.get(key, {})
            meta = ktdd_meta_map.get(rid, {})
            rel_ktdd = f"ktdd/{rid}.html"
            raw_path = self.raw_dir / rel_ktdd
            status = existing.get("status", "pending")
            if status == "pending" and raw_path.exists() and raw_path.stat().st_size > 512:
                status = "fetched"

            url_path = meta.get("url_path") or f"/kinh-thanh-doi-dap-{rid}"
            items[key] = {
                "item_type": "ktdd",
                "reading_id": rid,
                "slug": meta.get("slug", existing.get("slug", "")),
                "url": f"{self.base_url}{url_path}",
                "raw_rel_path": rel_ktdd,
                "status": status,
            }

        stats = self.state.recompute_stats()
        self.state.save()
        print(
            f"[{self.SOURCE_ID}:Step1] Đã khởi tạo 903 bài Thánh Ca ({len(mp3_ids)} bài có MP3) "
            f"& 100 bài KTĐĐ. Thống kê: {stats}"
        )
        return stats

    def step_2_fetch_raw(
        self,
        limit: Optional[int] = None,
        item_type: Optional[str] = None,
        fetch_musicxml: bool = True,
        force: bool = False,
    ) -> int:
        """
        Bước 2 (Fetch Raw HTML & MusicXML):
        - Tải `/thanh-ca-{id}?op=chords` (chứa cả Lời + Hợp âm - TRAP D3).
        - Tải `/Download/SheetMusic/{id}` với `allow_404=True` (bắt 404 êm ái - TRAP D7).
        - Tải `/kinh-thanh-doi-dap-{id}`.
        """
        if not self.state.data.get("items"):
            self.step_1_init_queue()

        fetched_now = 0
        self.state.install_signal_handler()
        try:
            for key, item in self.state.data["items"].items():
                if self.state.stop_requested:
                    break
                if item_type and item.get("item_type") != item_type:
                    continue

                raw_file = self.raw_dir / item["raw_rel_path"]
                if not force and item.get("status") in ("fetched", "parsed") and raw_file.exists():
                    continue

                if item["item_type"] == "hymn":
                    hid = item["hymn_id"]
                    url = item["url_chords"]
                    print(f"[{self.SOURCE_ID}:Step2] Đang tải Thánh Ca #{hid} (?op=chords): {url}...")
                    resp = self.client.request(url, expected_signatures=["lyric-content"])
                    atomic_write_text(raw_file, resp.text("utf-8"))

                    # Trích xuất slug từ final_url nếu có chuyển hướng
                    m_slug = re.search(r"/thanh-ca-\d+/([^?#]+)", resp.final_url)
                    slug = m_slug.group(1) if m_slug else item.get("slug", "")

                    xml_status = item.get("musicxml_status", "pending")
                    if fetch_musicxml and (force or xml_status == "pending"):
                        xml_file = self.raw_dir / "musicxml" / f"{hid}.xml"
                        xml_resp = self.client.request(item["url_musicxml"], allow_404=True)
                        if xml_resp.status == 200 and b"<score-partwise" in xml_resp.body[:1024]:
                            atomic_write_bytes(xml_file, xml_resp.body)
                            xml_status = "available"
                        else:
                            xml_status = "not_available"

                    self.state.update_item(
                        key,
                        {"status": "fetched", "slug": slug, "musicxml_status": xml_status},
                        auto_save=True,
                    )
                    fetched_now += 1

                elif item["item_type"] == "ktdd":
                    rid = item["reading_id"]
                    url = item["url"]
                    print(f"[{self.SOURCE_ID}:Step2] Đang tải KTĐĐ #{rid}: {url}...")
                    resp = self.client.request(url, expected_signatures=["lyric-content"])
                    atomic_write_text(raw_file, resp.text("utf-8"))
                    self.state.update_item(key, {"status": "fetched"}, auto_save=True)
                    fetched_now += 1

                if limit is not None and fetched_now >= limit:
                    print(f"[{self.SOURCE_ID}:Step2] Đã đạt giới hạn --limit {limit} mục.")
                    break
        finally:
            self.state.restore_signal_handler()

        print(f"[{self.SOURCE_ID}:Step2] Hoàn tất tải mới {fetched_now} mục. Thống kê: {self.state.recompute_stats()}")
        return fetched_now

    def step_3_parse_normalized(self, limit: Optional[int] = None) -> int:
        """
        Bước 3 (Parse & Normalize):
        Đọc các file HTML trong `raw/thanhca_httlvn/`, phân tích lời ca, hợp âm ChordPro và lượt đối đáp KTĐĐ.
        """
        if not self.state.data.get("items"):
            self.step_1_init_queue(discover_mp3_playlist=False)

        parsed_now = 0
        for key, item in self.state.data["items"].items():
            raw_file = self.raw_dir / item["raw_rel_path"]
            if not raw_file.exists():
                continue

            html_text = raw_file.read_text(encoding="utf-8")
            if item["item_type"] == "hymn":
                hid = item["hymn_id"]
                parsed = parse_hymn_chords_html(html_text, hid, slug=item.get("slug", ""))
                parsed["has_mp3"] = item.get("has_mp3", False)
                parsed["mp3_url"] = item.get("mp3_url")
                xml_file = self.raw_dir / "musicxml" / f"{hid}.xml"
                has_xml = xml_file.exists() and xml_file.stat().st_size > 256
                parsed["has_musicxml"] = has_xml
                parsed["musicxml_rel_path"] = f"musicxml/{hid}.xml" if has_xml else None

                # Chưng cất bản nhạc ký hiệu sang .abc (~1 KB) và .mid 4 bè SATB (~1.5 KB),
                # loại bỏ 100% thông tin chế bản đồ họa (Engraving Layout) của Finale!
                if has_xml:
                    abc_file = self.norm_dir / "abc" / f"{hid:03d}.abc"
                    mid_file = self.norm_dir / "midi" / f"{hid:03d}.mid"
                    distilled = distill_musicxml_file(
                        xml_path=xml_file,
                        hymn_id=hid,
                        title=parsed["title"],
                        abc_out_path=abc_file,
                        midi_out_path=mid_file,
                    )
                    parsed["symbolic_sheet"] = {
                        "key_signature": distilled["key_signature"],
                        "time_signature": distilled["time_signature"],
                        "tempo_bpm": distilled["tempo_bpm"],
                        "measure_count": distilled["measure_count"],
                        "abc_notation": distilled["abc_notation"],
                        "abc_rel_path": f"hymns/abc/{hid:03d}.abc",
                        "midi_rel_path": f"hymns/midi/{hid:03d}.mid",
                        "abc_size_bytes": distilled["abc_size_bytes"],
                        "midi_size_bytes": distilled["midi_size_bytes"],
                    }
                else:
                    parsed["symbolic_sheet"] = None

                out_file = self.norm_dir / "hymns" / f"{hid:03d}.json"
                atomic_write_json(out_file, parsed)
                self.state.update_item(
                    key,
                    {
                        "status": "parsed",
                        "title": parsed["title"],
                        "has_chords": parsed["has_chords"],
                        "stanza_count": parsed["stanza_count"],
                    },
                    auto_save=False,
                )
                parsed_now += 1

            elif item["item_type"] == "ktdd":
                rid = item["reading_id"]
                parsed = parse_responsive_reading_html(html_text, rid, slug=item.get("slug", ""))
                out_file = self.norm_dir / "ktdd" / f"{rid:03d}.json"
                atomic_write_json(out_file, parsed)
                self.state.update_item(
                    key,
                    {
                        "status": "parsed",
                        "title": parsed["title"],
                        "turn_count": parsed["turn_count"],
                    },
                    auto_save=False,
                )
                parsed_now += 1

            if limit is not None and parsed_now >= limit:
                break

        self.state.save()
        print(f"[{self.SOURCE_ID}:Step3] Đã phân tích cú pháp {parsed_now} mục. Thống kê: {self.state.recompute_stats()}")
        return parsed_now

