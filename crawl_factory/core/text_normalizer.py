"""
Bộ chuẩn hóa văn bản, mã hóa tiếng Việt 1925 và đường dẫn media (`text_normalizer.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/technical-design-and-anti-blocking.md`
- `crawl_factory/sources/docs/tinlanh-com.md` (TRAP B2: Ký tự Eth U+00D0)
- `crawl_factory/sources/docs/vietchristian.md` (TRAP D1: Double-UTF8 Mojibake, TRAP D2: U+00D0)
- `crawl_factory/sources/docs/kinhthanh-httlvn.md` (TRAP A5: Ngắt dòng thơ, TRAP A6: Backslash URL)
"""

from __future__ import annotations
import html
import re
import unicodedata
from typing import Optional


def normalize_vietnamese_1925(text: str, preserve_newlines: bool = True) -> str:
    """
    Chuẩn hóa văn bản Tiếng Việt (đặc biệt cho Kinh Thánh Bản Truyền Thống 1925 & Thánh Ca):
    1. Giải mã HTML entities (`&#225;`, `&nbsp;`, `&emsp;`...).
    2. Đưa về chuẩn Unicode dựng sẵn (NFC).
    3. Sửa lỗi Bẫy TRAP B2 / D2: Thay thế ký tự Latin Capital/Small Letter Eth (`Ð` U+00D0, `ð` U+00F0)
       hay gặp trên `GetBible vietnamese.json` và `vietchristian.com` về đúng chữ `Đ`/`đ` tiếng Việt (`U+0110`/`U+0111`).
    4. Thu gọn khoảng trắng ngang (`[ \\t\\u00a0\\u2003]+`) nhưng bảo toàn ký tự xuống dòng thơ `\\n`
       nếu `preserve_newlines=True`.
    5. TUYỆT ĐỐI KHÔNG tự ý sửa từ cổ của Bản 1925 (như 'nhứt', 'sanh', 'bèn', 'phân rẽ').
    """
    if not text:
        return ""
    # 1. Giải mã HTML entities
    s = html.unescape(text)
    # 2. Chuẩn hóa Unicode NFC
    s = unicodedata.normalize("NFC", s)
    # 3. Sửa lỗi ký tự Eth (U+00D0 / U+00F0) -> Đ / đ (U+0110 / U+0111)
    s = s.replace("\u00d0", "\u0110").replace("\u00f0", "\u0111")
    # 4. Chuẩn hóa dấu ngắt dòng
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    if preserve_newlines:
        lines = [re.sub(r"[ \t\u00a0\u2002\u2003]+", " ", ln).strip() for ln in s.split("\n")]
        return "\n".join(ln for ln in lines if ln)
    else:
        return re.sub(r"\s+", " ", s).strip()


def fix_double_utf8(corrupted_text: str) -> str:
    """
    Khôi phục chuỗi bị lỗi Mã hóa kép UTF-8 (Double-Encoded UTF-8 Mojibake - TRAP D1)
    trên `vietchristian.com/kinhthanh/tklk/tklk.xml` và các file `.dat`.

    Ví dụ:
        'ThÃ¡nh Kinh LÆ°á»£c Kháº£o' -> 'Thánh Kinh Lược Khảo'
    """
    if not corrupted_text:
        return ""
    try:
        repaired = corrupted_text.encode("cp1252").decode("utf-8")
        return normalize_vietnamese_1925(repaired)
    except (UnicodeEncodeError, UnicodeDecodeError):
        def _repair_chunk(m: re.Match) -> str:
            chunk = m.group(0)
            try:
                return chunk.encode("cp1252").decode("utf-8")
            except Exception:
                return chunk

        repaired = re.sub(r"[\x80-\xff\u0100-\u203a]+", _repair_chunk, corrupted_text)
        return normalize_vietnamese_1925(repaired)


def normalize_media_path(raw_path: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    """
    Chuẩn hóa đường dẫn Audio/Media bị chứa dấu gạch chéo ngược kiểu Windows (`\\`)
    trên `kinhthanh.httlvn.org` và `thanhca.httlvn.org` (TRAP A6 & TRAP D6).

    Ví dụ:
        '\\Audio\\VI1934\\1-ms-nguyen-thi\\sa\\1.mp3'
        -> 'https://kinhthanh.httlvn.org/Audio/VI1934/1-ms-nguyen-thi/sa/1.mp3'

        'https://audio.httlvn.org/TC/thanh-ca\\mp3/1.mp3'
        -> 'https://audio.httlvn.org/TC/thanh-ca/mp3/1.mp3'
    """
    if not raw_path:
        return None
    cleaned = raw_path.strip().replace("\\", "/")
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    if base_url:
        base = base_url.rstrip("/")
        if not cleaned.startswith("/"):
            cleaned = "/" + cleaned
        return base + cleaned
    return cleaned


def normalize_strong_code(raw_code: Optional[str]) -> Optional[str]:
    """
    Chuẩn hóa mã số Strong (TRAP C1): cắt bỏ các chữ số 0 thừa ở đầu để đồng nhất
    khóa chính giữa `EN_KJV` (`H07225`, `H0430`) và `ORIG_WLC` (`H7225`, `H430`).

    Ví dụ:
        'H07225' -> 'H7225'
        'G03056' -> 'G3056'
    """
    if not raw_code:
        return None
    m = re.match(r"^\s*([HGhg])0*(\d+)[a-zA-Z]?\s*$", raw_code)
    if not m:
        return raw_code.strip().upper()
    return f"{m.group(1).upper()}{int(m.group(2))}"

