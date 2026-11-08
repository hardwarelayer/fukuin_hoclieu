"""
Bộ phân tích `.shtml` của `www.tinlanh.com` và Thuật toán Biểu quyết Đa số 2/3 (`sources/tinlanh_com/parser.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/tinlanh-com.md` (Mục 2 & 3: TRAP B1, B2, B3 & 3-Way Majority Voting)

Xử lý 3 Bẫy Runtime:
- TRAP B1: Phát hiện và loại bỏ lỗi dấu gạch nối OCR trên `tinlanh.com` (`Đức-Giê hô-va` tại `thithien23.shtml`)
  nhờ biểu quyết đa số 2/3 với `kinhthanh.httlvn.org` và `GetBible vietnamese.json`.
- TRAP B2: Chuẩn hóa ký tự `Ð` (`U+00D0` Eth) trong `GetBible vietnamese.json` về `Đ` (`U+0110`).
- TRAP B3: Bổ sung nội dung của 16 câu khuyết Tân Ước (`Ma-thi-ơ 17:21`...) từ `GetBible vietnamese.json`.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import re

from crawl_factory.core.usfm_books import BY_USFM
from crawl_factory.core.text_normalizer import normalize_vietnamese_1925

# Mỗi dòng câu Kinh Thánh trong file .shtml của tinlanh.com có dạng:
# "1 Ban đầu Đức Chúa Trời dựng nên trời đất.<br>"
SHTML_VERSE_LINE_RE = re.compile(
    r"(?:^|<br\s*/?>)\s*(\d+)\s+([^<\r\n]+?)\s*(?=<br\s*/?>|$)",
    re.IGNORECASE | re.MULTILINE,
)


def parse_tinlanh_shtml(html_text: str, usfm_book: str, chapter_num: int) -> Dict[str, Any]:
    """
    Trích xuất danh sách câu Kinh Thánh từ file `.shtml` của `www.tinlanh.com`.
    """
    book_spec = BY_USFM[usfm_book]
    # Cắt từ sau thẻ <span class="bread">...</span> để tránh dính số trong menu đầu trang
    m_start = re.search(r"</span>\s*</div>", html_text, re.I)
    body_part = html_text[m_start.end():] if m_start else html_text

    verses: List[Dict[str, Any]] = []
    seen_v = set()
    for m in SHTML_VERSE_LINE_RE.finditer(body_part):
        v_num = int(m.group(1))
        if v_num in seen_v:
            continue
        v_text = normalize_vietnamese_1925(m.group(2), preserve_newlines=False)
        if not v_text:
            continue
        seen_v.add(v_num)
        verses.append({
            "verse_id": f"{usfm_book}.{chapter_num}.{v_num}",
            "verse": v_num,
            "text": v_text,
        })

    return {
        "source": "tinlanh_com",
        "usfm": usfm_book,
        "book_nr": book_spec.book_nr,
        "chapter": chapter_num,
        "verse_count": len(verses),
        "verses": verses,
    }


def _strip_punctuation_for_vote(text: str) -> str:
    """Chuẩn hóa nhẹ khoảng trắng quanh dấu câu để so khớp nội dung từ vựng và dấu gạch nối."""
    s = normalize_vietnamese_1925(text.replace("\n", " "), preserve_newlines=False)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    return s


def resolve_verse_3way(
    v_httlvn: Optional[str],
    v_tinlanh: Optional[str],
    v_getbible: Optional[str],
    verse_id: str,
) -> Dict[str, Any]:
    """
    Biểu quyết Đa số 2/3 (3-Way Majority Voting) giữa 3 nguồn Bản Truyền Thống 1925:
    - `v_httlvn`: kinhthanh.httlvn.org (Nguồn chính, giữ nguyên dòng thơ `\\n`)
    - `v_tinlanh`: www.tinlanh.com (`.shtml`)
    - `v_getbible`: api.getbible.net/v2/vietnamese.json (đã sửa `Ð` U+00D0 -> `Đ` U+0110)
    """
    a_raw = v_httlvn or ""
    a_flat = _strip_punctuation_for_vote(a_raw)
    b_flat = _strip_punctuation_for_vote(v_tinlanh or "")
    c_flat = _strip_punctuation_for_vote(v_getbible or "")

    if a_flat and a_flat == b_flat == c_flat:
        return {"status": "UNANIMOUS_3_OF_3", "chosen_text": a_raw, "discrepancy": None}

    if a_flat and (a_flat == b_flat or a_flat == c_flat):
        return {"status": "MAJORITY_HTTLVN_2_OF_3", "chosen_text": a_raw, "discrepancy": None}

    if b_flat and b_flat == c_flat and a_flat != b_flat:
        return {
            "status": "CONSENSUS_TINLANH_GETBIBLE_2_OF_3",
            "chosen_text": b_flat,
            "discrepancy": {
                "verse_id": verse_id,
                "httlvn": a_flat,
                "tinlanh": b_flat,
                "getbible": c_flat,
            },
        }

    # Nếu chỉ khác dấu chấm câu (: vs ;) nhưng từ vựng và gạch nối giống hệt nhau
    words_a = re.sub(r"[,.;:!?\"'”’“‘]", "", a_flat)
    words_b = re.sub(r"[,.;:!?\"'”’“‘]", "", b_flat)
    words_c = re.sub(r"[,.;:!?\"'”’“‘]", "", c_flat)
    if words_a and (words_a == words_b or words_a == words_c):
        return {"status": "LEXICAL_MATCH_2_OF_3", "chosen_text": a_raw, "discrepancy": None}

    return {
        "status": "NEEDS_REVIEW_ALL_3_DIFFER",
        "chosen_text": a_raw or c_flat or b_flat,
        "discrepancy": {
            "verse_id": verse_id,
            "httlvn": a_flat,
            "tinlanh": b_flat,
            "getbible": c_flat,
        },
    }

