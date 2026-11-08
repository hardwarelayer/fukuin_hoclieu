"""
Bộ phân tích dữ liệu tĩnh & bảng đối chiếu từ `vietchristian.com` (`sources/vietchristian/parser.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/vietchristian.md` (TRAP D1, D2, D9, D10)

Xử lý các Bẫy Runtime đã xác minh:
- TRAP D1: Khôi phục lỗi Double-Encoded UTF-8 Mojibake trong `tklk.xml` bằng `fix_double_utf8()`.
- TRAP D2: Sửa ký tự `Ð` (`U+00D0` Eth) về `Đ` (`U+0110`) trong `ktdd.txt` (70 bài) & `thanhca.txt` (511 bài).
- TRAP D10: Bóc tách bảng ánh xạ số bài Thánh Ca 2 hệ phái (`hid=0`, `hid=1`) kèm tên Tiếng Anh gốc
  (`original_title_en`) để nối chéo sang Thánh Ca Nhật `Sanbika 1954`.
"""

from __future__ import annotations
from typing import Any, Dict, List
import re

from crawl_factory.core.text_normalizer import fix_double_utf8, normalize_vietnamese_1925


def parse_tklk_xml(raw_xml_text: str) -> List[Dict[str, Any]]:
    """
    Phân tích file `tklk.xml` sau khi khôi phục lỗi Double-UTF8 Mojibake (TRAP D1).
    """
    repaired_xml = fix_double_utf8(raw_xml_text)
    books: List[Dict[str, Any]] = []
    for m_book in re.finditer(
        r'<book\s+title="([^"]+)"\s+code="([^"]+)"[^>]*>(.*?)</book>',
        repaired_xml,
        re.I | re.S,
    ):
        b_title = normalize_vietnamese_1925(m_book.group(1), preserve_newlines=False)
        b_code = m_book.group(2).strip()
        chapters = [
            normalize_vietnamese_1925(m_ch.group(1), preserve_newlines=False)
            for m_ch in re.finditer(r'<chapter\s+title="([^"]+)"', m_book.group(3), re.I)
        ]
        books.append({
            "title": b_title,
            "dat_code": b_code,
            "chapters": chapters,
        })
    return books


def parse_duong_linh_topics(kinhthanh_home_html: str) -> List[Dict[str, Any]]:
    """
    Trích xuất Bảng Câu Gốc Dưỡng Linh theo Tâm Trạng (`#divDL`) trên `/kinhthanh/`.
    """
    m_div = re.search(r'<div\s+id="divDL"[^>]*>(.*?)</div>\s*</div>', kinhthanh_home_html, re.I | re.S)
    block = m_div.group(1) if m_div else kinhthanh_home_html

    topics: List[Dict[str, Any]] = []
    for m_row in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", block, re.I | re.S):
        tds = re.findall(r"<td\b[^>]*>(.*?)</td>", m_row.group(1), re.I | re.S)
        if len(tds) >= 2:
            mood = normalize_vietnamese_1925(re.sub(r"<[^>]+>", " ", tds[0]), preserve_newlines=False)
            refs_raw = normalize_vietnamese_1925(re.sub(r"<[^>]+>", " ", tds[1]), preserve_newlines=False)
            if mood and refs_raw and mood.lower() not in ("chủ đề", "tâm trạng"):
                topics.append({
                    "mood_vi": mood,
                    "scripture_refs_display": [r.strip() for r in refs_raw.split(";") if r.strip()],
                })
    return topics


def parse_hymn_index_result_asp(html_text: str, hymnal_id: int) -> List[Dict[str, Any]]:
    """
    Phân tích bảng kết quả từ `POST /thanhca/result.asp` (`vn=1&Searchtype=index&hid=0|1` - TRAP D10)
    để lấy số bài, tên bài Tiếng Việt và tên bài Tiếng Anh nguyên gốc (`original_title_en`).
    """
    entries: List[Dict[str, Any]] = []
    for m_tr in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", html_text, re.I | re.S):
        tds = [
            normalize_vietnamese_1925(re.sub(r"<[^>]+>", " ", td), preserve_newlines=False)
            for td in re.findall(r"<td\b[^>]*>(.*?)</td>", m_tr.group(1), re.I | re.S)
        ]
        if len(tds) >= 2 and tds[0].isdigit():
            entries.append({
                "hymnal_id": hymnal_id,
                "number": int(tds[0]),
                "title_vi": tds[1],
                "original_title_en": tds[2] if len(tds) >= 3 and tds[2] else None,
                "author_or_key": tds[3] if len(tds) >= 4 and tds[3] else None,
            })
    return entries

