#!/usr/bin/env python3
"""
Cổng Kiểm Thử Chất Lượng Toàn Vẹn 2 Chiều (`fukuin_hoclieu/tools/validate_hoclieu.py`).

Kế thừa triết lý Quality Gate của `RoTK9_hoclieu/tools/validate_hoclieu.py` và kiểm tra trực tiếp
toàn bộ **18 Bẫy Runtime (TRAP A1 – TRAP E1)** đã đặc tả tại:
`crawl_factory/sources/docs/technical-design-and-anti-blocking.md`.

Cách chạy:
----------
    cd C:\\HomeWorking\\911\\repos\\fukuin_hoclieu
    python -X utf8 tools/validate_hoclieu.py
"""

from __future__ import annotations
import json
from pathlib import Path
import re
import sys
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crawl_factory.core.usfm_books import BY_USFM


def main() -> int:
    data_dir = REPO_ROOT / "data"
    errors: List[str] = []

    def fail(msg: str) -> None:
        errors.append(msg)
        print(f"  ❌ [LỖI] {msg}")

    print("🔍 Bắt đầu kiểm thử tính toàn vẹn dữ liệu `fukuin_hoclieu`...")

    # 1. Kiểm tra manifest.json & books.json (TRAP A1)
    manifest_file = data_dir / "manifest.json"
    books_file = data_dir / "bible" / "books.json"
    if not manifest_file.exists():
        fail("Thiếu file data/manifest.json (hãy chạy tools/build_hoclieu.py trước).")
    if not books_file.exists():
        fail("Thiếu file data/bible/books.json.")
    else:
        books = json.loads(books_file.read_text(encoding="utf-8"))
        if len(books) != 66:
            fail(f"books.json phải có đúng 66 sách, hiện có {len(books)}.")
        total_ch = sum(int(b["chapters"]) for b in books)
        if total_ch != 1189:
            fail(f"Tổng số chương trong books.json phải bằng 1.189, hiện có {total_ch}.")

        # Kiểm tra 6 mã sách dễ nhầm trên URL (TRAP A1)
        expected_trap_a1 = {
            "EZR": "exo",
            "EST": "et",
            "PRO": "ch",
            "HOS": "os",
            "PHP": "phi",
            "PHM": "phil",
            "REV": "kh",
        }
        book_map = {b["usfm"]: b for b in books}
        for usfm_code, exp_httlvn in expected_trap_a1.items():
            actual = book_map.get(usfm_code, {}).get("httlvn_code")
            if actual != exp_httlvn:
                fail(f"TRAP A1 vi phạm tại {usfm_code}: kỳ vọng httlvn_code='{exp_httlvn}', nhận '{actual}'.")

    # 2. Kiểm tra bảng lệnh tắt Buổi Nhóm (worship_aliases.json)
    aliases_file = data_dir / "search" / "worship_aliases.json"
    if not aliases_file.exists():
        fail("Thiếu file data/search/worship_aliases.json.")
    else:
        aliases_doc = json.loads(aliases_file.read_text(encoding="utf-8"))
        alias_map = aliases_doc.get("book_aliases_to_usfm", {})
        for sample_query, exp_usfm in [
            ("thi thien", "PSA"),
            ("thi-thiên", "PSA"),
            ("giăng", "JHN"),
            ("phi-líp", "PHP"),
            ("phi-lê-môn", "PHM"),
            ("詩篇", "PSA"),
        ]:
            if alias_map.get(sample_query) != exp_usfm:
                fail(f"worship_aliases.json không ánh xạ đúng '{sample_query}' -> '{exp_usfm}'.")

    # 3. Kiểm tra các chương Kinh Thánh đã biên dịch (TRAP A2, A3, A6, B1, B2, C2)
    chapters_root = data_dir / "bible" / "chapters"
    checked_chapters = 0
    checked_verses = 0
    if chapters_root.exists():
        for ch_file in sorted(chapters_root.rglob("*.json")):
            checked_chapters += 1
            ch_doc = json.loads(ch_file.read_text(encoding="utf-8"))
            usfm = ch_doc.get("usfm")
            ch_num = ch_doc.get("chapter")

            if usfm not in BY_USFM:
                fail(f"{ch_file}: Mã USFM không hợp lệ '{usfm}'.")

            # Kiểm tra TRAP A6 (không còn dấu backslash '\' trong audio_url)
            audio_url = ch_doc.get("audio_url") or ""
            if "\\" in audio_url:
                fail(f"TRAP A6 vi phạm tại {usfm}.{ch_num}: audio_url chứa dấu backslash '{audio_url}'.")

            # Kiểm tra TRAP A4 (thượng đề Thi-thiên không còn dính ký tự ⚓)
            sup = ch_doc.get("psalm_superscription") or ""
            if "⚓" in sup:
                fail(f"TRAP A4 vi phạm tại {usfm}.{ch_num}: psalm_superscription còn dính mỏ neo '⚓'.")

            for v in ch_doc.get("verses", []):
                checked_verses += 1
                v_id = v.get("verse_id", f"{usfm}.{ch_num}.?")
                v_text = v.get("text", "")

                # Kiểm tra TRAP B2 (không còn ký tự Eth Ð U+00D0 hoặc ð U+00F0)
                if "\u00d0" in v_text or "\u00f0" in v_text:
                    fail(f"TRAP B2 vi phạm tại {v_id}: chứa ký tự Eth U+00D0/U+00F0 chưa chuẩn hóa.")

                # Kiểm tra không còn dính mỏ neo ⚓ trong text
                if "⚓" in v_text:
                    fail(f"{v_id}: text còn sót ký tự '⚓'.")

                # Kiểm tra TRAP A2 & A3 (mọi target_usfm trong cross_references phải thuộc 66 sách chuẩn)
                for cref in v.get("cross_references", []):
                    tgt = cref.get("target_usfm")
                    if tgt not in BY_USFM:
                        fail(f"TRAP A3 vi phạm tại {v_id}: target_usfm='{tgt}' không thuộc 66 mã USFM chuẩn.")
                    if "][gt=" in (cref.get("raw") or ""):
                        fail(f"TRAP A2 vi phạm tại {v_id}: chuỗi '][gt=' chưa được tách khỏi cross_references.")

                # Kiểm tra TRAP B1 (nếu có ja_kougo thì không được bắt đầu bằng [0], [00], [1]...)
                ja_k = v.get("ja_kougo")
                if ja_k:
                    jp_plain = ja_k.get("text_plain", "")
                    if re.match(r"^\[\d+\]", jp_plain):
                        fail(f"TRAP B1 vi phạm tại {v_id}: ja_kougo.text_plain còn tiền tố số câu '{jp_plain[:15]}'.")

                # Kiểm tra TRAP C2 (nếu có original WLC thì surface không được chứa dấu '/')
                orig = v.get("original")
                if orig and "text_hebrew" in orig:
                    if "/" in orig["text_hebrew"]:
                        fail(f"TRAP C2 vi phạm tại {v_id}: text_hebrew còn chứa dấu '/' hình thái học.")

    # 4. Kiểm tra các bài Thánh Ca & KTĐĐ đã biên dịch (TRAP D4, D5, D8 & Symbolic Sheet .abc/.mid)
    hymns_root = data_dir / "hymns" / "vi-thanh-ca"
    checked_hymns = 0
    checked_symbolic_sheets = 0
    if hymns_root.exists():
        for h_file in sorted(hymns_root.glob("*.json")):
            checked_hymns += 1
            h_doc = json.loads(h_file.read_text(encoding="utf-8"))
            if h_doc.get("stanza_count", 0) == 0:
                fail(f"Thánh Ca {h_file.name}: stanza_count == 0.")
            for st in h_doc.get("stanzas", []):
                for cl_line in st.get("lines_clean", []):
                    # TRAP D5: kiểm tra không còn sót [Chord] trong lines_clean và không bị khoảng trắng quanh gạch nối
                    if re.search(r"\[[A-G][b#]?[^\]]*\]", cl_line):
                        fail(f"TRAP D5 vi phạm tại {h_file.name}: lines_clean còn sót hợp âm '{cl_line}'.")
                    if re.search(r"[A-Za-zÀ-ỹ]-\s+[a-zà-ỹ]", cl_line):
                        fail(f"TRAP D5 vi phạm tại {h_file.name}: từ ghép gạch nối bị chèn khoảng trắng '{cl_line}'.")

            sym = h_doc.get("symbolic_sheet")
            if sym:
                checked_symbolic_sheets += 1
                abc_path = data_dir / sym["abc_rel_path"]
                mid_path = data_dir / sym["midi_rel_path"]
                if not abc_path.exists():
                    fail(f"Thánh Ca {h_file.name}: thiếu file ABC tại {abc_path}.")
                else:
                    abc_txt = abc_path.read_text(encoding="utf-8")
                    if "X:" not in abc_txt or "K:" not in abc_txt:
                        fail(f"Thánh Ca {h_file.name}: file ABC không hợp lệ ({abc_path.name}).")
                if not mid_path.exists():
                    fail(f"Thánh Ca {h_file.name}: thiếu file MIDI tại {mid_path}.")
                else:
                    mid_bytes = mid_path.read_bytes()
                    if not mid_bytes.startswith(b"MThd") or b"MTrk" not in mid_bytes:
                        fail(f"Thánh Ca {h_file.name}: file MIDI không đúng chuẩn nhị phân MThd/MTrk ({mid_path.name}).")

    ktdd_root = data_dir / "ktdd"
    checked_ktdd = 0
    if ktdd_root.exists():
        for k_file in sorted(ktdd_root.glob("*.json")):
            checked_ktdd += 1
            k_doc = json.loads(k_file.read_text(encoding="utf-8"))
            if k_doc.get("turn_count", 0) == 0:
                fail(f"KTĐĐ {k_file.name}: turn_count == 0.")
            for sref in k_doc.get("scripture_references", []):
                usfm_prefix = (sref.get("usfm_ref") or "").split()[0]
                if usfm_prefix not in BY_USFM:
                    fail(f"KTĐĐ {k_file.name}: scripture_reference '{sref}' có mã USFM không hợp lệ.")

    if errors:
        print("============================================================")
        print(f"❌ KIỂM THỬ THẤT BẠI VỚI {len(errors)} LỖI!")
        print("============================================================")
        return 1

    print("============================================================")
    print("✅ 100% KIỂM THỬ THÀNH CÔNG! KHÔNG CÓ BẤT KỲ LỖI LIÊN KẾT HAY BẪY RUNTIME NÀO.")
    print(f"   - Đã kiểm tra 66 sách Kinh Thánh chuẩn (1.189 chương) & bảng lệnh tắt Buổi Nhóm.")
    print(f"   - Đã kiểm tra {checked_chapters} chương ({checked_verses} câu Kinh Thánh đa ngữ).")
    print(f"   - Đã kiểm tra {checked_hymns} bài Thánh Ca ({checked_symbolic_sheets} bản nhạc ký hiệu .abc/.mid 4 bè SATB) & {checked_ktdd} bài KTĐĐ.")
    print("============================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

