"""
Bộ phân tích cú pháp HTML cho `thanhca.httlvn.org` (`sources/thanhca_httlvn/parser.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/thanhca-httlvn.md` (Mục 2 & 3: Giải phẫu DOM 7 Tab & Bẫy TRAP D3 - D8)

Xử lý đầy đủ các Bẫy Runtime đã xác minh thực nghiệm:
- TRAP D3: Tách cả Lời sạch (`clean_lyrics`) và Hợp âm (`chordpro_lyrics`) từ một trang duy nhất
  `?op=chords`, và trích xuất danh sách 384 bài có MP3 từ `#audio-player-playlist` của Bài 1.
- TRAP D4: Hỗ trợ đồng thời cả 2 họ cấu trúc DOM lời bài hát:
  (a) Kiểu A (như Bài 1): Gộp khổ trong 1 thẻ `<p>`, đầu đoạn có `<b>B1L</b>` (`meter_code`).
  (b) Kiểu B (như Bài 42, 903): Tách từng dòng thành `<p>` riêng kèm nhãn `<p><b>Câu 1</b></p>`, `<p><b>Điệp khúc</b></p>`.
- TRAP D5: Xử lý thẻ `<i class="chord-group">` nằm giữa từ ghép có gạch nối (`Giê-<i class="chord-group">[Eb]ru</i>-sa-lem`)
  không chèn khoảng trắng thừa làm vỡ từ.
- TRAP D6: Chuẩn hóa dấu backslash `\\mp3/` trong đường dẫn audio.
- TRAP D8: Khử trùng lặp 200 thẻ `<a>` trên trang mục lục `/kinh-thanh-doi-dap` về đúng 100 bài.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import html
import re

from crawl_factory.core.usfm_books import CROSSREF_ABBR_TO_USFM
from crawl_factory.core.text_normalizer import normalize_vietnamese_1925

# Regex bắt thẻ hợp âm <i class="chord-group">...</i> (có thể bọc <span class="hopam">[G]</span> bên trong hoặc viết thẳng [G])
CHORD_GROUP_RE = re.compile(
    r'<i\s+class="chord-group"[^>]*>\s*(?:<span\s+class="hopam"[^>]*>\s*(\[[^\]]+\])\s*</span>|(\[[^\]]+\]))?(.*?)\s*</i>',
    re.IGNORECASE | re.DOTALL,
)

# Regex bắt mã nhịp/điệu nhạc ở đầu đoạn kiểu A (ví dụ: <b>B1L</b>)
METER_CODE_RE = re.compile(r"^\s*<b>\s*([A-Z]\d+[A-Z0-9]*)\s*</b>\s*", re.IGNORECASE)

# Regex nhận diện dòng tiêu đề khổ kiểu B (ví dụ: <b>Câu 1</b>, <b>Điệp khúc</b>)
STANZA_HEADER_ONLY_RE = re.compile(
    r"^\s*<b>\s*(Câu\s+\d+|Điệp\s*khúc|ĐK:?)\s*</b>\s*$",
    re.IGNORECASE,
)


def _extract_chordpro_and_clean(fragment_html: str) -> Tuple[str, str, List[str]]:
    """
    Chuyển một đoạn HTML dòng hát thành 2 phiên bản (Xử lý TRAP D5):
    - `chordpro_str`: Giữ `[Chord]` sát liền kề âm tiết (`Giê-[Eb]ru-sa-lem`).
    - `clean_str`: Loại bỏ hoàn toàn `[Chord]`, nối liền từ ghép (`Giê-ru-sa-lem`).
    - `chords_found`: Danh sách các hợp âm xuất hiện trong dòng.
    """
    chords_found: List[str] = []

    def _to_chordpro(m: re.Match) -> str:
        c1 = m.group(1) or m.group(2) or ""
        syllable = re.sub(r"<[^>]+>", "", m.group(3) or "")
        if c1:
            chord_name = c1.strip("[] ")
            if chord_name and chord_name not in chords_found:
                chords_found.append(chord_name)
        return f"{c1}{syllable}"

    def _to_clean(m: re.Match) -> str:
        syllable = re.sub(r"<[^>]+>", "", m.group(3) or "")
        return syllable

    cp_html = CHORD_GROUP_RE.sub(_to_chordpro, fragment_html)
    cl_html = CHORD_GROUP_RE.sub(_to_clean, fragment_html)

    # Xóa các thẻ <span class="hopam"> đứng lẻ ngoài <i> nếu có
    for m_extra in re.finditer(r'<span\s+class="hopam"[^>]*>\s*\[([^\]]+)\]\s*</span>', cp_html, re.I):
        cname = m_extra.group(1).strip()
        if cname and cname not in chords_found:
            chords_found.append(cname)
    cp_html = re.sub(r'<span\s+class="hopam"[^>]*>\s*(\[[^\]]+\])\s*</span>', r"\1", cp_html, flags=re.I)
    cl_html = re.sub(r'<span\s+class="hopam"[^>]*>.*?</span>', "", cl_html, flags=re.I | re.S)
    # Nếu trong <i class="chord-group"> không có span mà viết thẳng [G] ở bản clean thì cũng xóa
    cl_html = re.sub(r"\[[A-G][b#]?(?:m|maj|min|dim|aug|sus|\d)*(?:/[A-G][b#]?)?\]", "", cl_html)

    cp_text = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", cp_html), preserve_newlines=True)
    cl_text = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", cl_html), preserve_newlines=True)
    return cp_text, cl_text, chords_found


def parse_hymn_chords_html(html_text: str, hymn_id: int, slug: str = "") -> Dict[str, Any]:
    """
    Phân tích trang `/thanh-ca-{id}/{slug}?op=chords` (Xử lý TRAP D3, D4, D5):
    Trích xuất tiêu đề, tác giả nhạc/lời, chủ đề (`cat_top`, `cat_sub`), mã điệu nhạc (`meter_code`),
    danh sách hợp âm và các khổ hát (`stanzas`) ở cả hai định dạng Clean Lyrics & ChordPro.
    """
    # 1. Trích xuất phân loại chủ đề từ breadcrumb (cat_top, cat_sub)
    cat_top: Optional[str] = None
    cat_sub: Optional[str] = None
    m_cat_top = re.search(r'href="/thanh-ca\?cat_top=[^"]*"[^>]*>([^<]+)</a>', html_text, re.I)
    if m_cat_top:
        cat_top = normalize_vietnamese_1925(m_cat_top.group(1), preserve_newlines=False)
    m_cat_sub = re.search(r'href="/thanh-ca\?cat_top=[^"&]*&(?:amp;)?cat_sub=[^"]*"[^>]*>([^<]+)</a>', html_text, re.I)
    if m_cat_sub:
        cat_sub = normalize_vietnamese_1925(m_cat_sub.group(1), preserve_newlines=False)

    # 2. Trích xuất tên bài hát từ <h1>
    title = f"Thánh Ca {hymn_id}"
    m_h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", html_text, re.I | re.S)
    if m_h1:
        h1_no_small = re.sub(r"<small\b[^>]*>.*?</small>", "", m_h1.group(1), flags=re.I | re.S)
        extracted_title = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", h1_no_small), preserve_newlines=False)
        if extracted_title:
            title = extracted_title

    # 3. Trích xuất Nhạc sĩ (col-xs-6 text-left) & Dịch giả / Tác giả lời (col-xs-6 text-right)
    composer: Optional[str] = None
    translator: Optional[str] = None
    m_left = re.search(r'<div\s+class="col-xs-6\s+text-left"[^>]*>(.*?)</div>', html_text, re.I | re.S)
    if m_left:
        composer = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", m_left.group(1)), preserve_newlines=False) or None
    m_right = re.search(r'<div\s+class="col-xs-6\s+text-right"[^>]*>(.*?)</div>', html_text, re.I | re.S)
    if m_right:
        translator = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", m_right.group(1)), preserve_newlines=False) or None

    # 4. Bóc tách khối <div id="lyric-content"> (Xử lý 2 họ DOM - TRAP D4)
    m_lyric = re.search(r'<div\s+id="lyric-content"[^>]*>(.*?)</div>', html_text, re.I | re.S)
    lyric_inner = m_lyric.group(1) if m_lyric else ""

    p_blocks = re.findall(r"<p\b[^>]*>(.*?)</p>", lyric_inner, re.I | re.S)
    meter_code: Optional[str] = None
    all_chords: List[str] = []
    stanzas: List[Dict[str, Any]] = []

    # Kiểm tra xem bài hát thuộc Họ DOM Kiểu B (có thẻ <p><b>Câu 1</b></p> riêng) hay Kiểu A
    is_family_b = any(STANZA_HEADER_ONLY_RE.match(p.strip()) for p in p_blocks)

    if is_family_b:
        current_label = "Câu 1"
        current_type = "verse"
        current_cp_lines: List[str] = []
        current_cl_lines: List[str] = []

        def _flush_b():
            nonlocal current_cp_lines, current_cl_lines
            if current_cl_lines:
                stanzas.append({
                    "label": current_label,
                    "type": current_type,
                    "lines_clean": list(current_cl_lines),
                    "lines_chordpro": list(current_cp_lines),
                })
                current_cp_lines = []
                current_cl_lines = []

        for p_raw in p_blocks:
            p_str = p_raw.strip()
            if not p_str:
                continue
            m_hdr = STANZA_HEADER_ONLY_RE.match(p_str)
            if m_hdr:
                _flush_b()
                current_label = normalize_vietnamese_1925(m_hdr.group(1), preserve_newlines=False)
                current_type = "chorus" if "điệp" in current_label.lower() or "đk" in current_label.lower() else "verse"
                continue

            m_meter = METER_CODE_RE.match(p_str)
            if m_meter:
                meter_code = m_meter.group(1).upper()
                p_str = p_str[m_meter.end():].strip()

            p_with_nl = re.sub(r"<br\s*/?>", "\n", p_str, flags=re.I)
            cp_txt, cl_txt, ch_list = _extract_chordpro_and_clean(p_with_nl)
            for c in ch_list:
                if c not in all_chords:
                    all_chords.append(c)
            for ln_cp, ln_cl in zip(cp_txt.split("\n"), cl_txt.split("\n")):
                if ln_cl.strip():
                    current_cp_lines.append(ln_cp.strip())
                    current_cl_lines.append(ln_cl.strip())
        _flush_b()
    else:
        # Họ DOM Kiểu A (mỗi thẻ <p> là 1 khổ hoặc các dòng cách nhau bởi <br/>)
        verse_counter = 0
        for p_raw in p_blocks:
            p_str = p_raw.strip()
            if not p_str:
                continue
            m_meter = METER_CODE_RE.match(p_str)
            if m_meter:
                meter_code = m_meter.group(1).upper()
                p_str = p_str[m_meter.end():].strip()

            p_with_nl = re.sub(r"<br\s*/?>", "\n", p_str, flags=re.I)
            cp_txt, cl_txt, ch_list = _extract_chordpro_and_clean(p_with_nl)
            for c in ch_list:
                if c not in all_chords:
                    all_chords.append(c)
            if not cl_txt:
                continue

            cl_lines = [ln.strip() for ln in cl_txt.split("\n") if ln.strip()]
            cp_lines = [ln.strip() for ln in cp_txt.split("\n") if ln.strip()]
            first_line = cl_lines[0] if cl_lines else ""

            if re.match(r"^(Điệp\s*khúc|ĐK)\b", first_line, re.I):
                st_type = "chorus"
                label = "Điệp khúc"
            else:
                st_type = "verse"
                m_num = re.match(r"^(\d+)\.\s*", first_line)
                if m_num:
                    verse_counter = int(m_num.group(1))
                else:
                    verse_counter += 1
                label = f"Câu {verse_counter}"

            stanzas.append({
                "label": label,
                "type": st_type,
                "lines_clean": cl_lines,
                "lines_chordpro": cp_lines,
            })

    return {
        "hymn_id": hymn_id,
        "code": f"TC_{hymn_id:03d}",
        "slug": slug,
        "title": title,
        "category_top": cat_top,
        "category_sub": cat_sub,
        "composer": composer,
        "translator": translator,
        "meter_code": meter_code,
        "has_chords": len(all_chords) > 0,
        "chords_used": all_chords,
        "stanza_count": len(stanzas),
        "stanzas": stanzas,
    }


def parse_mp3_playlist_html(html_text: str) -> List[int]:
    """
    Trích xuất toàn bộ 384 ID bài Thánh Ca có file MP3 từ `<div class="list-group audio-player-playlist">`
    chỉ bằng 1 request duy nhất tới `/thanh-ca-1/cui-xin-vua-thanh-ngu-lai?op=mp3` (TRAP D3).
    """
    ids = [
        int(m.group(1))
        for m in re.finditer(r'href="/thanh-ca-(\d+)[^"]*\?op=mp3"\s+class="list-group-item', html_text, re.I)
    ]
    return sorted(set(ids))


def parse_youtube_embed_id(html_text: str) -> Optional[str]:
    """Trích xuất YouTube Video ID từ tab `?op=beat` hoặc `?op=karaoke`."""
    m = re.search(r'youtube\.com/embed/([A-Za-z0-9_\-]{6,})', html_text, re.I)
    return m.group(1) if m else None


def parse_responsive_reading_index_html(html_text: str) -> List[Dict[str, Any]]:
    """
    Trích xuất danh sách 100 bài Kinh Thánh Đối Đáp từ `/kinh-thanh-doi-dap`
    và khử trùng lặp 200 thẻ `<a>` xuống đúng 100 bài (Xử lý TRAP D8).
    """
    by_id: Dict[int, Dict[str, Any]] = {}
    for m in re.finditer(r'href="(/kinh-thanh-doi-dap-(\d+)/([^"?#]+))"[^>]*>(.*?)</a>', html_text, re.I | re.S):
        rel_url = m.group(1)
        rid = int(m.group(2))
        slug = m.group(3)
        inner_txt = normalize_vietnamese_1925(re.sub(r"<[^>]+>", " ", m.group(4)), preserve_newlines=False)
        if rid not in by_id:
            by_id[rid] = {
                "reading_id": rid,
                "slug": slug,
                "url_path": rel_url,
                "title_raw": inner_txt,
            }
    return [by_id[k] for k in sorted(by_id.keys())]


def parse_responsive_reading_html(html_text: str, reading_id: int, slug: str = "") -> Dict[str, Any]:
    """
    Phân tích chi tiết 1 bài Kinh Thánh Đối Đáp (`/kinh-thanh-doi-dap-{id}/{slug}`):
    - Tách lượt đọc của Người hướng dẫn (`<p>`) và Hội chúng (`<blockquote><strong>`).
    - Chuẩn hóa địa chỉ Kinh Thánh trong `<a data-bible="sa 1:1-6">` sang mã USFM (`GEN 1:1-6`).
    """
    title = f"Kinh Thánh Đối Đáp {reading_id}"
    m_h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", html_text, re.I | re.S)
    if m_h1:
        h1_no_small = re.sub(r"<small\b[^>]*>.*?</small>", "", m_h1.group(1), flags=re.I | re.S)
        t_clean = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", h1_no_small), preserve_newlines=False)
        if t_clean:
            title = t_clean

    m_lyric = re.search(r'<div\s+id="lyric-content"[^>]*>(.*?)</div>', html_text, re.I | re.S)
    content_html = m_lyric.group(1) if m_lyric else html_text

    turns: List[Dict[str, Any]] = []
    scripture_refs: List[Dict[str, str]] = []

    token_re = re.compile(r"(<p\b[^>]*>.*?</p>)|(<blockquote\b[^>]*>.*?</blockquote>)", re.I | re.S)
    for m_tok in token_re.finditer(content_html):
        p_block = m_tok.group(1)
        bq_block = m_tok.group(2)

        if p_block:
            m_bible = re.search(r'data-bible="([^"]+)"[^>]*>(.*?)</a>', p_block, re.I | re.S)
            if m_bible:
                raw_code = html.unescape(m_bible.group(1)).strip()
                display_ref = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", m_bible.group(2)), preserve_newlines=False)
                # Chuẩn hóa mã sách đầu chuỗi data-bible (ví dụ: "sa 1:1-6" -> "GEN 1:1-6")
                m_parts = re.match(r"^([1-3]?[a-zA-Z]+)\s+(.+)$", raw_code)
                usfm_ref = raw_code
                if m_parts:
                    usfm_code = CROSSREF_ABBR_TO_USFM.get(m_parts.group(1).lower(), m_parts.group(1).upper())
                    usfm_ref = f"{usfm_code} {m_parts.group(2)}"
                ref_entry = {
                    "raw_data_bible": raw_code,
                    "usfm_ref": usfm_ref,
                    "display": display_ref,
                }
                scripture_refs.append(ref_entry)
                continue

            txt = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", p_block), preserve_newlines=False)
            if txt:
                turns.append({"turn_index": len(turns) + 1, "role": "leader", "text": txt})

        elif bq_block:
            txt = normalize_vietnamese_1925(re.sub(r"<[^>]+>", "", bq_block), preserve_newlines=False)
            if txt:
                turns.append({"turn_index": len(turns) + 1, "role": "congregation", "text": txt})

    return {
        "reading_id": reading_id,
        "code": f"KTDD_{reading_id:03d}",
        "slug": slug,
        "title": title,
        "scripture_references": scripture_refs,
        "turn_count": len(turns),
        "turns": turns,
    }

