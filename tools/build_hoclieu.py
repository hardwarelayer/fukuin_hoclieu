#!/usr/bin/env python3
"""
Công cụ Chưng Cất & Tổng Hợp Học Liệu (`fukuin_hoclieu/tools/build_hoclieu.py`).

Nhiệm vụ:
---------
Đọc dữ liệu đã phân tích từ `crawl_factory/normalized/` (theo hợp đồng tại
`crawl_factory/sources/docs/distill-contract.md`), kết hợp đa ngôn ngữ (`VI1934` + `tinlanh_com`/`GetBible`
3-Way Consensus + `JA_KOUGO` Ruby + `JA_BUNGO` + `ORIG_WLC`/`ORIG_GNT`), sinh chỉ mục tìm kiếm nhanh
buổi nhóm (`data/search/worship_aliases.json`) và xuất bản vào `fukuin_hoclieu/data/`.

Cách chạy:
----------
    cd C:\\HomeWorking\\911\\repos\\fukuin_hoclieu
    python -X utf8 tools/build_hoclieu.py
"""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawl_factory.core.state_manager import atomic_write_bytes, atomic_write_json, atomic_write_text, utc_now_iso
from crawl_factory.core.usfm_books import BIBLE_BOOKS_66, TOTAL_BIBLE_CHAPTERS, strip_accents


def build_books_catalog(data_dir: Path) -> List[Dict[str, Any]]:
    """Xuất danh mục chuẩn 66 sách Kinh Thánh (`data/bible/books.json`)."""
    books_out: List[Dict[str, Any]] = []
    for b in BIBLE_BOOKS_66:
        books_out.append({
            "book_nr": b.book_nr,
            "usfm": b.usfm,
            "testament": b.testament,
            "httlvn_code": b.httlvn_code,
            "crossref_abbr": b.crossref_abbr,
            "tinlanh_slug": b.tinlanh_slug,
            "wlc_osis": b.wlc_osis,
            "morphgnt_prefix": b.morphgnt_prefix,
            "chapters": b.chapters,
            "name_vi": b.name_vi_1925,
            "slug_vi": b.slug_vi,
            "name_en": b.name_en,
            "name_ja": b.name_ja,
        })
    atomic_write_json(data_dir / "bible" / "books.json", books_out)
    return books_out


def build_worship_aliases(data_dir: Path) -> Dict[str, Any]:
    """
    Sinh bảng ánh xạ Tìm Kiếm Nhanh Buổi Nhóm (`data/search/worship_aliases.json`).
    Xem tài liệu: `fukuin/docs/tim-kiem-nhanh-buoi-nhom-va-kien-truc-da-cong.md`.
    Hỗ trợ gõ nhanh:
    - 'Thánh Ca 42', 'TC 42', 'tc42' -> /thanh-ca/42/
    - 'KTĐĐ 1', 'ktdd 1', 'đối đáp 1' -> /kinh-thanh-doi-dap/1/
    - 'Thi Thiên 90', 'thi 90', 'Giăng 3:16', '詩篇 23' -> /kinh-thanh/{slug_vi}/{chapter}/
    """
    book_aliases: Dict[str, str] = {}
    for b in BIBLE_BOOKS_66:
        candidates = {
            b.usfm.lower(),
            b.httlvn_code.lower(),
            b.crossref_abbr.lower(),
            b.tinlanh_slug.lower(),
            b.slug_vi.lower(),
            b.slug_vi.replace("-", "").lower(),
            b.name_vi_1925.lower(),
            strip_accents(b.name_vi_1925).lower(),
            re.sub(r"[^a-z0-9\s]", " ", strip_accents(b.name_vi_1925).lower()).strip(),
            b.name_en.lower(),
            b.name_ja,
        }
        for alias in candidates:
            clean_alias = " ".join(alias.split())
            if clean_alias:
                book_aliases[clean_alias] = b.usfm

    payload = {
        "generated_at": utc_now_iso(),
        "command_prefixes": {
            "hymn_vi": ["thanh ca", "thánh ca", "tc", "tctl", "bai hat", "bài hát"],
            "hymn_ja": ["sanbika", "讃美歌", "さんびか", "sbk"],
            "ktdd": ["ktdd", "ktđđ", "kinh thanh doi dap", "kinh thánh đối đáp", "doi dap", "đối đáp"],
        },
        "book_aliases_to_usfm": book_aliases,
    }
    atomic_write_json(data_dir / "search" / "worship_aliases.json", payload)
    return payload


import re


def compile_normalized_chapters(norm_dir: Path, data_dir: Path) -> Dict[str, int]:
    """
    Hợp nhất các chương đã phân tích từ:
    - `normalized/kinhthanh_httlvn/VI1934/{USFM}/{ch}.json`
    - `normalized/tinlanh_com/{USFM}/{ch}.json` (nếu có kết quả bỏ phiếu 3 nguồn)
    - `normalized/open_multilingual/{ja_kougo|ja_bungo|orig_wlc|orig_gnt}/{USFM}/{ch}.json`
    vào `data/bible/chapters/{USFM}/{ch}.json`.
    """
    httlvn_root = norm_dir / "kinhthanh_httlvn" / "VI1934"
    tinlanh_root = norm_dir / "tinlanh_com"
    multilang_root = norm_dir / "open_multilingual"

    compiled_chapters = 0
    total_verses = 0

    if not httlvn_root.exists():
        return {"compiled_chapters": 0, "total_verses": 0}

    for usfm_dir in sorted(httlvn_root.iterdir()):
        if not usfm_dir.is_dir():
            continue
        usfm = usfm_dir.name
        for ch_file in sorted(usfm_dir.glob("*.json"), key=lambda p: int(p.stem)):
            ch_num = int(ch_file.stem)
            chapter_doc = json.loads(ch_file.read_text(encoding="utf-8"))

            # Ghép kết quả đối chiếu 3 nguồn nếu có
            tl_file = tinlanh_root / usfm / f"{ch_num}.json"
            vote_map: Dict[int, Dict[str, Any]] = {}
            if tl_file.exists():
                tl_doc = json.loads(tl_file.read_text(encoding="utf-8"))
                for v_row in tl_doc.get("verses", []):
                    vote_map[int(v_row["verse"])] = v_row

            # Ghép bản Tiếng Nhật 口語訳 1955 (có Ruby) và 文語訳 1917 nếu có
            kougo_file = multilang_root / "ja_kougo" / usfm / f"{ch_num}.json"
            kougo_map: Dict[int, Dict[str, Any]] = {}
            kougo_sup: str | None = None
            if kougo_file.exists():
                k_doc = json.loads(kougo_file.read_text(encoding="utf-8"))
                kougo_sup = k_doc.get("psalm_superscription_ruby_html")
                for v_row in k_doc.get("verses", []):
                    kougo_map[int(v_row["verse"])] = v_row

            bungo_file = multilang_root / "ja_bungo" / usfm / f"{ch_num}.json"
            bungo_map: Dict[int, str] = {}
            if bungo_file.exists():
                b_doc = json.loads(bungo_file.read_text(encoding="utf-8"))
                for v_row in b_doc.get("verses", []):
                    bungo_map[int(v_row["verse"])] = v_row.get("text", "")

            # Ghép ngôn ngữ gốc WLC / GNT nếu có
            wlc_file = multilang_root / "orig_wlc" / usfm / f"{ch_num}.json"
            gnt_file = multilang_root / "orig_gnt" / usfm / f"{ch_num}.json"
            orig_map: Dict[int, Dict[str, Any]] = {}
            if wlc_file.exists():
                w_doc = json.loads(wlc_file.read_text(encoding="utf-8"))
                w_verses = w_doc.get("verses", [])
                vi_v_count = len(chapter_doc.get("verses", []))
                # Xử lý TRAP C2 (Item 4): Ở sách Thi-thiên (PSA), bản Hê-bơ-rơ WLC đánh số Thượng đề là câu 1 (hoặc câu 1..2 ở Thi 51),
                # làm lệch số câu đi +1 hoặc +2 so với bản Tin Lành (VI1934 / KJV / JA_KOUGO).
                offset = 0
                if usfm == "PSA" and len(w_verses) > vi_v_count and (len(w_verses) - vi_v_count) in (1, 2):
                    offset = len(w_verses) - vi_v_count
                    chapter_doc["psalm_superscription_hebrew"] = w_verses[:offset]
                for v_row in w_verses[offset:]:
                    aligned_v_num = int(v_row["verse"]) - offset
                    orig_map[aligned_v_num] = v_row
            elif gnt_file.exists():
                g_doc = json.loads(gnt_file.read_text(encoding="utf-8"))
                for v_row in g_doc.get("verses", []):
                    orig_map[int(v_row["verse"])] = v_row

            if kougo_sup:
                chapter_doc["psalm_superscription_ja_ruby"] = kougo_sup

            for v_obj in chapter_doc.get("verses", []):
                v_num = int(v_obj["verse"])
                if v_num in vote_map:
                    v_obj["verification_status"] = vote_map[v_num]["vote_status"]
                if v_num in kougo_map:
                    v_obj["ja_kougo"] = {
                        "text_plain": kougo_map[v_num]["text_plain"],
                        "text_ruby_html": kougo_map[v_num]["text_ruby_html"],
                        "ruby_tokens": kougo_map[v_num]["ruby_tokens"],
                    }
                if v_num in bungo_map:
                    v_obj["ja_bungo_text"] = bungo_map[v_num]
                if v_num in orig_map:
                    v_obj["original"] = orig_map[v_num]

            out_path = data_dir / "bible" / "chapters" / usfm / f"{ch_num}.json"
            atomic_write_json(out_path, chapter_doc)
            compiled_chapters += 1
            total_verses += len(chapter_doc.get("verses", []))

    return {"compiled_chapters": compiled_chapters, "total_verses": total_verses}


def compile_hymns_and_ktdd(norm_dir: Path, data_dir: Path) -> Dict[str, int]:
    """Sao chép & làm giàu các bài Thánh Ca và Kinh Thánh Đối Đáp sang `data/`."""
    tc_norm = norm_dir / "thanhca_httlvn"
    vc_norm = norm_dir / "vietchristian"

    # Đọc bảng tên tiếng Anh bài Thánh Ca từ vietchristian (nếu đã tải)
    en_title_map: Dict[int, str] = {}
    for hid_idx in (0, 1):
        f_idx = vc_norm / f"hymn_index_hid{hid_idx}.json"
        if f_idx.exists():
            rows = json.loads(f_idx.read_text(encoding="utf-8"))
            for r in rows:
                if r.get("original_title_en") and r["number"] not in en_title_map:
                    en_title_map[int(r["number"])] = r["original_title_en"]

    hymn_count = 0
    symbolic_sheet_count = 0
    hymns_dir = tc_norm / "hymns"
    if hymns_dir.exists():
        for h_file in sorted(hymns_dir.glob("*.json")):
            h_doc = json.loads(h_file.read_text(encoding="utf-8"))
            hid = int(h_doc["hymn_id"])
            if hid in en_title_map:
                h_doc["original_title_en"] = en_title_map[hid]

            # Sao chép file .abc và .mid 4 bè SATB sang data/hymns/{abc|midi}/
            abc_src = tc_norm / "abc" / f"{hid:03d}.abc"
            mid_src = tc_norm / "midi" / f"{hid:03d}.mid"
            if abc_src.exists() and mid_src.exists():
                atomic_write_text(data_dir / "hymns" / "abc" / f"{hid:03d}.abc", abc_src.read_text(encoding="utf-8"))
                atomic_write_bytes(data_dir / "hymns" / "midi" / f"{hid:03d}.mid", mid_src.read_bytes())
                symbolic_sheet_count += 1

            atomic_write_json(data_dir / "hymns" / "vi-thanh-ca" / h_file.name, h_doc)
            hymn_count += 1

    ktdd_count = 0
    ktdd_dir = tc_norm / "ktdd"
    if ktdd_dir.exists():
        for k_file in sorted(ktdd_dir.glob("*.json")):
            k_doc = json.loads(k_file.read_text(encoding="utf-8"))
            atomic_write_json(data_dir / "ktdd" / k_file.name, k_doc)
            ktdd_count += 1

    return {
        "compiled_hymns": hymn_count,
        "compiled_symbolic_sheets": symbolic_sheet_count,
        "compiled_ktdd": ktdd_count,
    }


def main() -> int:
    norm_dir = REPO_ROOT / "crawl_factory" / "normalized"
    data_dir = REPO_ROOT / "data"

    books = build_books_catalog(data_dir)
    aliases = build_worship_aliases(data_dir)
    bible_stats = compile_normalized_chapters(norm_dir, data_dir)
    hymn_stats = compile_hymns_and_ktdd(norm_dir, data_dir)

    manifest = {
        "project": "fukuin_hoclieu",
        "generated_at": utc_now_iso(),
        "canonical_books": len(books),
        "canonical_total_chapters": TOTAL_BIBLE_CHAPTERS,
        "worship_book_aliases": len(aliases["book_aliases_to_usfm"]),
        "compiled_chapters": bible_stats["compiled_chapters"],
        "compiled_verses": bible_stats["total_verses"],
        "compiled_hymns": hymn_stats["compiled_hymns"],
        "compiled_symbolic_sheets": hymn_stats["compiled_symbolic_sheets"],
        "compiled_ktdd": hymn_stats["compiled_ktdd"],
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    manifest["sha256_signature"] = hashlib.sha256(manifest_bytes).hexdigest()
    atomic_write_json(data_dir / "manifest.json", manifest)

    print("============================================================")
    print("✅ BUILD HỌC LIỆU FUKUIN HOÀN TẤT!")
    print(f"   - Danh mục Sách Kinh Thánh chuẩn : {len(books)} sách ({TOTAL_BIBLE_CHAPTERS} chương)")
    print(f"   - Bảng lệnh tắt Buổi Nhóm        : {len(aliases['book_aliases_to_usfm'])} tên gọi sách")
    print(f"   - Số chương Kinh Thánh đã biên dịch : {bible_stats['compiled_chapters']} chương ({bible_stats['total_verses']} câu)")
    print(f"   - Số bài Thánh Ca / KTĐĐ đã biên dịch: {hymn_stats['compiled_hymns']} Thánh Ca, {hymn_stats['compiled_ktdd']} KTĐĐ")
    print("============================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
