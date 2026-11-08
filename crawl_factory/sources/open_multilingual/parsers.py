r"""
Các bộ phân tích cú pháp (Parsers) cho nguồn mở đa ngôn ngữ (`sources/open_multilingual/parsers.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/multilingual-open-bibles-hymns.md` (Mục 2: Giải phẫu 6 Bẫy Runtime)

Xử lý đầy đủ các Bẫy Runtime đã xác minh thực nghiệm:
- TRAP B1 (`Bolls.life JPKJV.json` - `JA_KOUGO`): Khắc phục lỗi lệch số câu `+1` hoặc `+2` ở sách Thi-thiên
  do tiền tố `[0]` và `[00]` (Thượng đề) chiếm `"verse": 1, 2`. Luôn đọc số câu chuẩn từ `[N]` ở đầu `"text"`,
  và chuyển `<i>Kanji</i><sup>,reading</sup>` sang HTML5 `<ruby>Kanji<rt>reading</rt></ruby>` + `ruby_tokens`.
- TRAP C1 (`eBible.org` USFM - `EN_WEB` & `EN_KJV`): Bóc tách `\f...\f*` và `\x...\x*` trước khi đọc lời câu;
  cấm dùng mã Strong lỗi của `WEB`; chỉ lấy mã Strong chuẩn từ `EN_KJV` và cắt số `0` thừa ở đầu (`H07225` -> `H7225`).
- TRAP C2 (`OpenScriptures WLC` - `ORIG_WLC`): Phân tích `lemma="c/d/776"`, `"1254 a"` sang mã Strong `"H776"`, `"H1254"`;
  loại bỏ dấu `/` phân tách hình thái học trong chữ Hê-bơ-rơ hiển thị (`בְּ/רֵאשִׁ֖ית` -> `בְּרֵאשִׁ֖ית`) và nối `x-maqqef` (`־`).
- TRAP C3 (`MorphGNT SBLGNT` - `ORIG_GNT`): Giải mã cột 1 `BBCCVV` (`010101` = Book 40 MAT, Chap 1, Verse 1) và
  gom từ nguyên thể Hy Lạp (`lemma`) theo từng câu.
- TRAP E1 (`Sanbika 1954`): Chuẩn hóa cấu trúc JSON lời ca từ `kanichi-sanbika/songs.json`.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import re

from crawl_factory.core.text_normalizer import normalize_strong_code

# --- 1. PARSER CHO BOLLS.LIFE JPKJV.JSON (JA_KOUGO - TRAP B1) ---
BOLLS_PREFIX_RE = re.compile(r"^\[(0+|[1-9]\d*)\]\s*(.*)$", re.DOTALL)
BOLLS_RUBY_RE = re.compile(r"<i>([^<]+)</i><sup>,([^<]+)</sup>")


def parse_bolls_jpkjv_chapter(raw_items: List[Dict[str, Any]], usfm_book: str, chapter_num: int) -> Dict[str, Any]:
    """
    Phân tích 1 chương Tiếng Nhật 口語訳 1955 từ `Bolls.life JPKJV.json` (Xử lý TRAP B1):
    - Tách `[0]`, `[00]` thành `psalm_superscription_ja`.
    - Lấy số câu chuẩn từ `[N]` (`N >= 1`) ở đầu `"text"` thay vì tin vào trường `"verse"` bị lệch.
    - Chuyển `<i>Kanji</i><sup>,reading</sup>` thành `<ruby>Kanji<rt>reading</rt></ruby>` và mảng `ruby_tokens`.
    """
    superscriptions_ruby: List[str] = []
    superscriptions_plain: List[str] = []
    verses: List[Dict[str, Any]] = []

    for item in raw_items:
        raw_text = (item.get("text") or "").strip()
        true_verse = int(item.get("verse", 0))

        m_pref = BOLLS_PREFIX_RE.match(raw_text)
        if m_pref:
            tag_num = m_pref.group(1)
            raw_text = m_pref.group(2).strip()
            if tag_num in ("0", "00"):
                superscriptions_ruby.append(BOLLS_RUBY_RE.sub(r"<ruby>\1<rt>\2</rt></ruby>", raw_text))
                superscriptions_plain.append(BOLLS_RUBY_RE.sub(r"\1", raw_text))
                continue
            else:
                true_verse = int(tag_num)

        ruby_tokens = [
            {"surface": m.group(1), "reading": m.group(2)}
            for m in BOLLS_RUBY_RE.finditer(raw_text)
        ]
        text_ruby_html = BOLLS_RUBY_RE.sub(r"<ruby>\1<rt>\2</rt></ruby>", raw_text)
        text_plain = BOLLS_RUBY_RE.sub(r"\1", raw_text)
        # Dọn các thẻ <br/> thừa nếu có
        text_plain = re.sub(r"<br\s*/?>", " ", text_plain).strip()

        verses.append({
            "verse_id": f"{usfm_book}.{chapter_num}.{true_verse}",
            "verse": true_verse,
            "text_plain": text_plain,
            "text_ruby_html": text_ruby_html,
            "ruby_tokens": ruby_tokens,
        })

    return {
        "version": "JA_KOUGO",
        "usfm": usfm_book,
        "chapter": chapter_num,
        "psalm_superscription_plain": " ".join(superscriptions_plain) if superscriptions_plain else None,
        "psalm_superscription_ruby_html": " ".join(superscriptions_ruby) if superscriptions_ruby else None,
        "verse_count": len(verses),
        "verses": verses,
    }


# --- 2. PARSER CHO USFM (EN_KJV & EN_WEB - TRAP C1) ---
USFM_FOOTNOTE_RE = re.compile(r"\\f\b.*?\\f\*", re.DOTALL)
USFM_CROSSREF_RE = re.compile(r"\\x\b.*?\\x\*", re.DOTALL)
USFM_WORD_STRONG_RE = re.compile(r'\\w\s+([^|\\]+?)(?:\|[^\\]*?\bstrong="([^"]+)"[^\\]*?)?\\w\*')
USFM_ADD_RE = re.compile(r"\\add\s+(.*?)\\add\*", re.DOTALL)


def parse_usfm_verse_line(raw_usfm_verse: str, extract_strongs: bool = True) -> Dict[str, Any]:
    """
    Phân tích nội dung 1 câu USFM (Xử lý TRAP C1):
    - Tách chú thích chân trang `\\f ... \\f*` ra mảng `footnotes` trước tiên.
    - Nếu `extract_strongs=True` (dùng cho `EN_KJV`): trích xuất danh sách `(word, strong_id)` đã chuẩn hóa
      (`H07225` -> `H7225`).
    - Nếu `extract_strongs=False` (bắt buộc cho `EN_WEB` do mã Strong tự động bị lỗi): chỉ lấy văn bản sạch.
    """
    footnotes: List[str] = []
    for m_fn in USFM_FOOTNOTE_RE.finditer(raw_usfm_verse):
        fn_raw = m_fn.group(0)
        fn_clean = re.sub(r"\\[a-z]+\*?", " ", fn_raw)
        fn_clean = re.sub(r"\s+", " ", fn_clean).strip(" +")
        if fn_clean:
            footnotes.append(fn_clean)

    no_notes = USFM_FOOTNOTE_RE.sub("", raw_usfm_verse)
    no_notes = USFM_CROSSREF_RE.sub("", no_notes)

    word_strong_tokens: List[Dict[str, str]] = []
    if extract_strongs:
        for m_w in USFM_WORD_STRONG_RE.finditer(no_notes):
            w_surface = m_w.group(1).strip()
            s_raw = m_w.group(2)
            if w_surface and s_raw:
                # Có thể có nhiều mã Strong cách nhau bởi khoảng trắng
                for code_part in s_raw.split():
                    norm_code = normalize_strong_code(code_part)
                    if norm_code and norm_code.startswith(("H", "G")):
                        word_strong_tokens.append({"word": w_surface, "strong": norm_code})

    # Thay \w word|strong="..."\w* bằng word
    clean = USFM_WORD_STRONG_RE.sub(r"\1", no_notes)
    # Thay \add word\add* bằng word
    clean = USFM_ADD_RE.sub(r"\1", clean)
    # Xóa các thẻ định dạng đoạn/thơ còn lại (\p, \q1, \q2, \b, \m...)
    clean = re.sub(r"\\[a-z]+\d*\*?\s*", " ", clean)
    clean = re.sub(r"\s+([,.;:!?])", r"\1", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    return {
        "text": clean,
        "footnotes": footnotes,
        "strong_tokens": word_strong_tokens if extract_strongs else [],
    }


# --- 3. PARSER CHO OPENSCRIPTURES WLC XML (ORIG_WLC - TRAP C2) ---
WLC_VERSE_RE = re.compile(r'<verse\s+osisID="([^"]+)"[^>]*>(.*?)</verse>', re.DOTALL)
WLC_TOKEN_RE = re.compile(
    r'(<w\b[^>]*>(.*?)</w>)|(<seg\s+type="([^"]+)"[^>]*>(.*?)</seg>)',
    re.DOTALL,
)


def parse_wlc_lemma(raw_lemma: str) -> Dict[str, Any]:
    """
    Phân tích thuộc tính `lemma` của OpenScriptures WLC (Xử lý TRAP C2):
    - Ví dụ `"b/7225"` -> `{"strong": "H7225", "prefixes": ["b"], "raw_lemma": "b/7225"}`
    - Ví dụ `"c/d/776"` -> `{"strong": "H776", "prefixes": ["c", "d"], "raw_lemma": "c/d/776"}`
    - Ví dụ `"1254 a"` -> `{"strong": "H1254", "prefixes": [], "homonym": "a", "raw_lemma": "1254 a"}`
    """
    parts = [p.strip() for p in raw_lemma.split("/") if p.strip()]
    prefixes = [p for p in parts[:-1] if not any(ch.isdigit() for ch in p)]
    main_part = parts[-1] if parts else ""
    m = re.match(r"^(\d+)\s*([a-zA-Z]?)$", main_part)
    strong_id = f"H{int(m.group(1))}" if m else None
    homonym = m.group(2) if (m and m.group(2)) else None
    return {
        "strong": strong_id,
        "prefixes": prefixes,
        "homonym": homonym,
        "raw_lemma": raw_lemma,
    }


def parse_wlc_xml_chapter(xml_text: str, wlc_osis_book: str, chapter_num: int, usfm_book: str) -> Dict[str, Any]:
    """
    Trích xuất toàn bộ các câu và từ gốc Hê-bơ-rơ của 1 chương từ file `wlc/{Book}.xml` (Xử lý TRAP C2).
    """
    prefix_target = f"{wlc_osis_book}.{chapter_num}."
    verses: List[Dict[str, Any]] = []

    for m_v in WLC_VERSE_RE.finditer(xml_text):
        osis_id = m_v.group(1)
        if not osis_id.startswith(prefix_target):
            continue
        v_num = int(osis_id.split(".")[-1])
        v_inner = m_v.group(2)

        tokens: List[Dict[str, Any]] = []
        display_pieces: List[str] = []

        for m_tok in WLC_TOKEN_RE.finditer(v_inner):
            w_full = m_tok.group(1)
            w_inner = m_tok.group(2)
            seg_full = m_tok.group(3)
            seg_type = m_tok.group(4)
            seg_inner = m_tok.group(5)

            if w_full:
                m_lem = re.search(r'\blemma="([^"]+)"', w_full)
                m_mor = re.search(r'\bmorph="([^"]+)"', w_full)
                raw_lemma = m_lem.group(1) if m_lem else ""
                morph = m_mor.group(1) if m_mor else ""
                surface_seg = re.sub(r"<[^>]+>", "", w_inner).strip()
                # Xóa dấu '/' phân tách hình thái học để hiển thị chữ Hê-bơ-rơ liền mạch (TRAP C2)
                surface_clean = surface_seg.replace("/", "")
                lem_info = parse_wlc_lemma(raw_lemma)

                tokens.append({
                    "surface": surface_clean,
                    "surface_segmented": surface_seg,
                    "strong": lem_info["strong"],
                    "prefixes": lem_info["prefixes"],
                    "morph": morph,
                })
                display_pieces.append(surface_clean)

            elif seg_full:
                if seg_type == "x-maqqef" and display_pieces:
                    # Nối từ trước với từ sau bằng dấu gạch nối Maqqef (־) không có khoảng trắng
                    display_pieces[-1] = display_pieces[-1] + (seg_inner or "־")
                elif seg_type == "x-sof-pasuq" and display_pieces:
                    display_pieces[-1] = display_pieces[-1] + (seg_inner or "׃")

        # Ghép chuỗi câu Hê-bơ-rơ (nếu mảnh trước kết thúc bằng Maqqef ־ thì không chèn khoảng trắng)
        hebrew_sentence = ""
        for piece in display_pieces:
            if not hebrew_sentence or hebrew_sentence.endswith("־"):
                hebrew_sentence += piece
            else:
                hebrew_sentence += " " + piece

        verses.append({
            "verse_id": f"{usfm_book}.{chapter_num}.{v_num}",
            "wlc_osis_id": osis_id,
            "verse": v_num,
            "text_hebrew": hebrew_sentence,
            "tokens": tokens,
        })

    return {
        "version": "ORIG_WLC",
        "usfm": usfm_book,
        "chapter": chapter_num,
        "verse_count": len(verses),
        "verses": verses,
    }


# --- 4. PARSER CHO MORPHGNT SBLGNT (ORIG_GNT - TRAP C3) ---
def parse_morphgnt_chapter_lines(
    txt_content: str,
    nt_book_index_1based: int,
    chapter_num: int,
    usfm_book: str,
) -> Dict[str, Any]:
    """
    Phân tích 1 chương Tân Ước Hy Lạp từ định dạng 7 cột của `MorphGNT` (Xử lý TRAP C3):
    Cột 1 `BBCCVV` (ví dụ `010101` = Sách Tân Ước số 01 `MAT`, Chương `01`, Câu `01`).
    """
    prefix_bcv = f"{nt_book_index_1based:02d}{chapter_num:02d}"
    by_verse: Dict[int, List[Dict[str, str]]] = {}

    for line in txt_content.splitlines():
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        bcv = parts[0]
        if not bcv.startswith(prefix_bcv):
            continue
        v_num = int(bcv[4:6])
        by_verse.setdefault(v_num, []).append({
            "pos": parts[1],
            "morph": parts[2],
            "surface_with_punct": parts[3],
            "surface_word": parts[4],
            "normalized": parts[5],
            "lemma": parts[6],
        })

    verses: List[Dict[str, Any]] = []
    for v_num in sorted(by_verse.keys()):
        toks = by_verse[v_num]
        greek_sentence = " ".join(t["surface_with_punct"] for t in toks)
        verses.append({
            "verse_id": f"{usfm_book}.{chapter_num}.{v_num}",
            "verse": v_num,
            "text_greek": greek_sentence,
            "tokens": toks,
        })

    return {
        "version": "ORIG_GNT",
        "usfm": usfm_book,
        "chapter": chapter_num,
        "verse_count": len(verses),
        "verses": verses,
    }
