"""
Bộ phân tích cú pháp HTML cho `kinhthanh.httlvn.org` (`sources/kinhthanh_httlvn/parser.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/kinhthanh-httlvn.md` (Mục 4 & 5: Giải phẫu DOM & 6 Bẫy Parser)

Xử lý đầy đủ 6 Bẫy Runtime đã xác minh:
- TRAP A1: Ánh xạ chuẩn 66 mã sách URL qua `core.usfm_books`.
- TRAP A2: Tách chuỗi `][gt=` trong thuộc tính `title` của `<a ...>⚓</a>` để phân biệt
  (a) 16 câu khuyết trong Tân Ước (`mat/17:21`...) và khôi phục thành bản ghi câu có cờ
      `is_omitted_in_critical_text = True`,
  (b) các địa chỉ tham chiếu chéo mở rộng (`es/53`, `ro/8`).
- TRAP A3: Chuẩn hóa mã sách viết tắt trong tooltip `⚓` (`Mac` -> `MRK`, `Kh` -> `REV`...).
- TRAP A4: Tách thẻ `<i>` Thượng đề Thi-thiên trong `<div class="title">` và bóc thẻ `<a>⚓</a>`
  lồng bên trong `<i>`.
- TRAP A5: Bảo toàn cấu trúc dòng thơ `<br/>&emsp;` thành `\\n` (`poetic_lines`), nhận diện ngắt khổ
  8 câu ở Thi-thiên 119 (`<br/>&emsp;<br/>` -> `is_stanza_break = True`) và dấu đổi vai `---` ở Nhã-ca.
- TRAP A6: Chuẩn hóa dấu backslash Windows `\\Audio\\...` trong đường dẫn MP3.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import html
import re

from crawl_factory.core.usfm_books import BY_USFM, CROSSREF_ABBR_TO_USFM
from crawl_factory.core.text_normalizer import normalize_media_path, normalize_vietnamese_1925

# Regex khớp một địa chỉ tham chiếu chéo đơn lẻ (ví dụ: "Mat 21:21", "1Co 13:2", "2Sa 12:1-15", "Lu 9:43b-45")
REF_ITEM_RE = re.compile(r"^([1-3]?[A-Za-z]+)\s+(\d+):([\d\-,\sa-c]+)$")
# Regex khớp địa chỉ kế thừa tên sách từ mục đứng trước sau dấu ';' (ví dụ: "Xu 30:13; 38:26" -> "38:26")
REF_CONTINUATION_RE = re.compile(r"^(\d+):([\d\-,\sa-c]+)$")

# Regex nhận diện ghi chú 16 câu khuyết Tân Ước nằm sau '][gt=' (TRAP A2)
OMITTED_VERSE_RE = re.compile(
    r"Có mấy bản cũ thêm (?:một )?câu\s+(\d+)\s+rằng:\s*(.+)",
    re.IGNORECASE | re.DOTALL,
)

# Regex bắt tất cả thẻ neo tham chiếu chéo <a ... title="...">⚓</a>
ANCHOR_TOOLTIP_RE = re.compile(
    r'<a\b[^>]*\btitle="([^"]*)"[^>]*>\s*⚓\s*</a>',
    re.IGNORECASE | re.DOTALL,
)

# Regex bắt đường dẫn Audio MP3 trong chương (TRAP A6)
AUDIO_SOURCE_RE = re.compile(
    r'<source\b[^>]*\bsrc="([^"]+\.mp3)"',
    re.IGNORECASE,
)

# Regex bắt các khối <div class="title">...</div> và <span class="verse {code}_{ch}_{v}">...</span> theo đúng thứ tự xuất hiện
TOKEN_BLOCK_RE = re.compile(
    r'(<div\s+class="title"[^>]*>.*?</div>)|(<span\s+class="verse\s+([a-z0-9]+)_(\d+)_(\d+)"[^>]*>(.*?)</span>)',
    re.IGNORECASE | re.DOTALL,
)


def parse_tooltip_title(raw_title: str) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """
    Phân tích thuộc tính `title` của thẻ `<a>⚓</a>` (Xử lý TRAP A2 & TRAP A3).

    Trả về bộ 3:
    - `cross_refs`: Danh sách các tham chiếu chéo đã chuẩn hóa sang mã USFM.
    - `footnotes`: Danh sách ghi chú văn bản học.
    - `omitted_verses`: Danh sách câu Kinh Thánh bị lược trong bản Critical Text (nếu có).
    """
    cross_refs: List[Dict[str, Any]] = []
    footnotes: List[str] = []
    omitted_verses: List[Dict[str, Any]] = []

    if not raw_title:
        return cross_refs, footnotes, omitted_verses

    unescaped = html.unescape(raw_title).strip()
    segments = [seg.strip() for seg in unescaped.split("][gt=") if seg.strip()]

    for seg in segments:
        # 1. Kiểm tra xem có phải ghi chú câu khuyết Tân Ước hay không (TRAP A2)
        m_omit = OMITTED_VERSE_RE.search(seg)
        if m_omit:
            clean_note = normalize_vietnamese_1925(seg, preserve_newlines=False)
            omit_v_num = int(m_omit.group(1))
            omit_v_text = normalize_vietnamese_1925(m_omit.group(2), preserve_newlines=False)
            footnotes.append(clean_note)
            omitted_verses.append({
                "verse": omit_v_num,
                "text": omit_v_text,
                "raw_note": clean_note,
            })
            continue

        # 2. Thử phân tích như danh sách các địa chỉ tham chiếu phân cách bởi ';'
        items = [it.strip() for it in seg.split(";") if it.strip()]
        parsed_batch: List[Dict[str, Any]] = []
        all_valid = True
        last_usfm_target: str | None = None
        for it in items:
            m_ref = REF_ITEM_RE.match(it)
            if m_ref:
                raw_abbr = m_ref.group(1).lower()
                usfm_target = CROSSREF_ABBR_TO_USFM.get(raw_abbr, raw_abbr.upper())
                last_usfm_target = usfm_target
                parsed_batch.append({
                    "raw": it,
                    "target_usfm": usfm_target,
                    "target_chapter": int(m_ref.group(2)),
                    "target_verses": m_ref.group(3).strip(),
                })
                continue

            m_cont = REF_CONTINUATION_RE.match(it)
            if m_cont and last_usfm_target:
                parsed_batch.append({
                    "raw": it,
                    "target_usfm": last_usfm_target,
                    "target_chapter": int(m_cont.group(1)),
                    "target_verses": m_cont.group(2).strip(),
                })
                continue

            all_valid = False
            break

        if all_valid and parsed_batch:
            cross_refs.extend(parsed_batch)
        else:
            footnotes.append(normalize_vietnamese_1925(seg, preserve_newlines=False))

    return cross_refs, footnotes, omitted_verses


def _strip_tags(raw_html: str) -> str:
    """Loại bỏ toàn bộ thẻ HTML và chuẩn hóa chuỗi tiếng Việt."""
    no_tags = re.sub(r"<[^>]+>", "", raw_html)
    return normalize_vietnamese_1925(no_tags, preserve_newlines=False)


def parse_title_div(title_div_html: str) -> Dict[str, Any]:
    """
    Phân tích khối `<div class="title">...</div>` (Xử lý TRAP A4):
    - Tách `<h2>` (tiêu đề đại phân đoạn), `<p>` (phạm vi đoạn), `<h3>` (tiêu đề phân đoạn).
    - Tách `<i>` (Thượng đề Thi-thiên nguyên bản Hê-bơ-rơ) và bóc tách các thẻ `<a>⚓</a>`
      lồng bên trong `<i>` trước khi lấy text.
    """
    headings: List[Dict[str, str]] = []
    superscription_text: str | None = None
    superscription_refs: List[Dict[str, Any]] = []

    for tag_name, role in (("h2", "major_section"), ("p", "section_scope"), ("h3", "section_title")):
        for m in re.finditer(rf"<{tag_name}\b[^>]*>(.*?)</{tag_name}>", title_div_html, re.I | re.S):
            cleaned_inner = ANCHOR_TOOLTIP_RE.sub("", m.group(1))
            txt = _strip_tags(cleaned_inner)
            if txt:
                headings.append({"type": role, "text": txt})

    # Xử lý thẻ <i> Thượng đề Thi-thiên (TRAP A4)
    m_sup = re.search(r"<i\b[^>]*>(.*?)</i>", title_div_html, re.I | re.S)
    if m_sup:
        sup_inner = m_sup.group(1)
        for m_anc in ANCHOR_TOOLTIP_RE.finditer(sup_inner):
            crefs, _, _ = parse_tooltip_title(m_anc.group(1))
            superscription_refs.extend(crefs)
        sup_no_anchor = ANCHOR_TOOLTIP_RE.sub("", sup_inner)
        txt_sup = _strip_tags(sup_no_anchor)
        if txt_sup:
            superscription_text = txt_sup

    return {
        "headings": headings,
        "psalm_superscription": superscription_text,
        "superscription_cross_refs": superscription_refs,
    }


def parse_httlvn_chapter_html(
    html_text: str,
    usfm_book: str,
    chapter_num: int,
    base_url: str = "https://kinhthanh.httlvn.org",
) -> Dict[str, Any]:
    """
    Phân tích toàn bộ trang HTML của 1 chương từ `kinhthanh.httlvn.org` thành cấu trúc JSON chuẩn.
    """
    book_spec = BY_USFM[usfm_book]

    # 1. Trích xuất đường dẫn Audio MP3 và sửa dấu backslash Windows (TRAP A6)
    m_audio = AUDIO_SOURCE_RE.search(html_text)
    audio_url = normalize_media_path(m_audio.group(1), base_url=base_url) if m_audio else None

    # 2. Thu hẹp phạm vi tìm kiếm vào khối <div id="{httlvn_code}_{chapter}"> nếu có
    div_id = f"{book_spec.httlvn_code}_{chapter_num}"
    m_container = re.search(
        rf'<div\s+id="{re.escape(div_id)}"[^>]*>(.*?)</div>\s*</div>',
        html_text,
        re.I | re.S,
    )
    target_html = m_container.group(1) if m_container else html_text

    pending_headings: List[Dict[str, str]] = []
    chapter_superscription: str | None = None
    chapter_superscription_refs: List[Dict[str, Any]] = []
    verses: List[Dict[str, Any]] = []

    for m_tok in TOKEN_BLOCK_RE.finditer(target_html):
        title_block = m_tok.group(1)
        verse_block = m_tok.group(2)

        if title_block:
            parsed_t = parse_title_div(title_block)
            pending_headings.extend(parsed_t["headings"])
            if parsed_t["psalm_superscription"]:
                chapter_superscription = parsed_t["psalm_superscription"]
                chapter_superscription_refs.extend(parsed_t["superscription_cross_refs"])
            continue

        if verse_block:
            v_num = int(m_tok.group(5))
            v_inner = m_tok.group(6)

            # Kiểm tra cờ đầu đoạn văn (&emsp;<sup>) và ngắt khổ Thi-thiên 119 (<br/>&emsp;<br/> - TRAP A5)
            is_para_start = bool(re.match(r"^\s*(?:&emsp;|\u2003)\s*<sup\b", v_inner, re.I))
            is_stanza_break = bool(
                re.search(r"<br\s*/?>\s*(?:&emsp;|\u2003)\s*<br\s*/?>\s*$", v_inner, re.I)
            )
            is_para_end = is_stanza_break or bool(re.search(r"<br\s*/?>\s*$", v_inner, re.I))

            # Bóc tách toàn bộ thẻ <a title="...">⚓</a> trong câu (TRAP A2 & TRAP A3)
            v_cross_refs: List[Dict[str, Any]] = []
            v_footnotes: List[str] = []
            v_omitted_following: List[Dict[str, Any]] = []

            for m_anc in ANCHOR_TOOLTIP_RE.finditer(v_inner):
                crefs, fnotes, omitted = parse_tooltip_title(m_anc.group(1))
                v_cross_refs.extend(crefs)
                v_footnotes.extend(fnotes)
                v_omitted_following.extend(omitted)

            # Loại bỏ thẻ <sup>số câu</sup> và các thẻ <a>⚓</a> khỏi nội dung câu
            cleaned = re.sub(r"<sup\b[^>]*>.*?</sup>", "", v_inner, flags=re.I | re.S)
            cleaned = ANCHOR_TOOLTIP_RE.sub("", cleaned)

            # Xử lý ngắt dòng thơ <br/>&emsp; ở giữa câu thành '\n' (TRAP A5)
            cleaned = re.sub(r"<br\s*/?>\s*(?:&emsp;|\u2003)+", "\n", cleaned, flags=re.I)
            # Loại bỏ các thẻ <br/> cuối câu và các thẻ HTML còn sót
            cleaned = re.sub(r"<br\s*/?>", " ", cleaned, flags=re.I)
            cleaned = re.sub(r"<[^>]+>", "", cleaned)

            text_normalized = normalize_vietnamese_1925(cleaned, preserve_newlines=True)
            poetic_lines = [ln for ln in text_normalized.split("\n") if ln] if "\n" in text_normalized else None

            verse_record: Dict[str, Any] = {
                "verse_id": f"{usfm_book}.{chapter_num}.{v_num}",
                "verse": v_num,
                "text": text_normalized,
                "poetic_lines": poetic_lines,
                "is_paragraph_start": is_para_start,
                "is_paragraph_end": is_para_end,
                "is_stanza_break": is_stanza_break,
                "is_omitted_in_critical_text": False,
                "section_headings": pending_headings if pending_headings else [],
                "cross_references": v_cross_refs,
                "textual_footnotes": v_footnotes,
            }
            pending_headings = []
            verses.append(verse_record)

            # Nếu mỏ neo ⚓ cuối câu này chứa câu Tân Ước bị lược (ví dụ mat/17:21 - TRAP A2),
            # khôi phục câu đó thành bản ghi kế tiếp để đồng bộ số câu 1-1 với KJV & GetBible!
            for omit_item in v_omitted_following:
                omit_v_num = omit_item["verse"]
                verses.append({
                    "verse_id": f"{usfm_book}.{chapter_num}.{omit_v_num}",
                    "verse": omit_v_num,
                    "text": f"[{omit_item['text']}]",
                    "footnote_only_text": omit_item["text"],
                    "poetic_lines": None,
                    "is_paragraph_start": False,
                    "is_paragraph_end": False,
                    "is_stanza_break": False,
                    "is_omitted_in_critical_text": True,
                    "section_headings": [],
                    "cross_references": [],
                    "textual_footnotes": [omit_item["raw_note"]],
                })

    return {
        "source": "kinhthanh_httlvn",
        "version": "VI1934",
        "book_nr": book_spec.book_nr,
        "usfm": usfm_book,
        "httlvn_code": book_spec.httlvn_code,
        "book_name_vi": book_spec.name_vi_1925,
        "chapter": chapter_num,
        "chapter_id": f"{usfm_book}.{chapter_num}",
        "audio_url": audio_url,
        "psalm_superscription": chapter_superscription,
        "superscription_cross_refs": chapter_superscription_refs,
        "verse_count": len(verses),
        "verses": verses,
    }
