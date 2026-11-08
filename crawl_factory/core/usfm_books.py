"""
Bảng chuẩn hóa 66 sách Kinh Thánh đa nguồn (`usfm_books.py`).

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/kinhthanh-httlvn.md` (Mục 3: Bảng 66 sách & TRAP A1, TRAP A3)
- `crawl_factory/sources/docs/multilingual-open-bibles-hymns.md`

LƯU Ý QUAN TRỌNG CHO TEAM PHÁT TRIỂN (TRAP A1):
Trên `kinhthanh.httlvn.org`, có 6 mã sách trên URL (`httlvn_code`) khác biệt hoàn toàn
với cách viết tắt thông thường. Tuyệt đối KHÔNG tự suy đoán mã sách mà phải tra qua
module này:
1. Ê-xơ-ra (`EZR`, sách 15)      -> `exo`  (KHÔNG phải `exr`; phân biệt `xu`=Xuất, `exo`=Ê-xơ-ra, `exe`=Ê-xê-chi-ên)
2. Ê-xơ-tê (`EST`, sách 17)      -> `et`   (KHÔNG phải `ext`)
3. Châm-ngôn (`PRO`, sách 20)    -> `ch`   (KHÔNG phải `cham`)
4. Ô-sê (`HOS`, sách 28)         -> `os`   (KHÔNG phải `ho`)
5. Phi-líp (`PHP`, sách 50)      -> `phi`  trong khi Phi-lê-môn (`PHM`, sách 57) -> `phil`!
6. Khải-huyền (`REV`, sách 66)   -> `kh`   (KHÔNG phải `khai`)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import re
import unicodedata


@dataclass(frozen=True)
class BookSpec:
    """Đặc tả bất biến của một sách Kinh Thánh xuyên suốt mọi nguồn dữ liệu."""
    book_nr: int                        # Số thứ tự chuẩn Tin Lành (1..66), khớp với GetBible & Bolls.life
    usfm: str                           # Mã chuẩn quốc tế USFM 3.0 (3 ký tự hoa: GEN..REV)
    testament: str                      # "OT" (1..39) hoặc "NT" (40..66)
    httlvn_code: str                    # Mã trên URL kinhthanh.httlvn.org (/doc-kinh-thanh/{httlvn_code}/{ch})
    crossref_abbr: str                  # Mã viết tắt trong tooltip ⚓ của kinhthanh.httlvn.org
    tinlanh_slug: str                   # Slug thư mục/file trên www.tinlanh.com
    wlc_osis: Optional[str]             # Mã file XML trong openscriptures/morphhb (Gen..Mal cho Cựu Ước)
    morphgnt_prefix: Optional[str]      # Tiền tố file trong morphgnt/sblgnt (61-Mt..87-Re cho Tân Ước)
    chapters: int                       # Tổng số chương chuẩn của sách
    name_vi_1925: str                   # Tên sách Tiếng Việt Bản Truyền Thống 1925
    slug_vi: str                        # Slug URL chuẩn trên web app fukuin (ví dụ: sang-the-ky)
    name_en: str                        # Tên sách Tiếng Anh (KJV / WEB)
    name_ja: str                        # Tên sách Tiếng Nhật (口語訳 / 文語訳)

    @property
    def tinlanh_testament_dir(self) -> str:
        """Tên thư mục Cựu/Tân Ước trên www.tinlanh.com."""
        return "cuuuoc" if self.testament == "OT" else "tanuoc"

    def httlvn_chapter_url(self, chapter: int, version: str = "VI1934") -> str:
        """Sinh URL đọc 1 chương trên kinhthanh.httlvn.org."""
        return f"https://kinhthanh.httlvn.org/doc-kinh-thanh/{self.httlvn_code}/{chapter}?v={version}"

    def tinlanh_chapter_url(self, chapter: int) -> str:
        """Sinh URL đọc 1 chương (.shtml) trên www.tinlanh.com."""
        return (
            f"https://www.tinlanh.com/thanhkinh/{self.tinlanh_testament_dir}/"
            f"{self.tinlanh_slug}/{self.tinlanh_slug}{chapter}.shtml"
        )


# Danh sách chuẩn 66 sách Kinh Thánh (39 Cựu Ước + 27 Tân Ước = 1.189 chương)
BIBLE_BOOKS_66: List[BookSpec] = [
    # --- CỰU ƯỚC (39 SÁCH - 929 CHƯƠNG) ---
    BookSpec(1, "GEN", "OT", "sa", "Sa", "sangtheky", "Gen", None, 50, "Sáng-thế Ký", "sang-the-ky", "Genesis", "創世記"),
    BookSpec(2, "EXO", "OT", "xu", "Xu", "xuatediptoky", "Exod", None, 40, "Xuất Ê-díp-tô Ký", "xuat-e-dip-to-ky", "Exodus", "出エジプト記"),
    BookSpec(3, "LEV", "OT", "le", "Le", "leviky", "Lev", None, 27, "Lê-vi Ký", "le-vi-ky", "Leviticus", "レビ記"),
    BookSpec(4, "NUM", "OT", "dan", "Dan", "dansoky", "Num", None, 36, "Dân-số Ký", "dan-so-ky", "Numbers", "民数記"),
    BookSpec(5, "DEU", "OT", "phu", "Phu", "phuctruyenluatleky", "Deut", None, 34, "Phục-truyền Luật-lệ Ký", "phuc-truyen-luat-le-ky", "Deuteronomy", "申命記"),
    BookSpec(6, "JOS", "OT", "gios", "Gios", "giosue", "Josh", None, 24, "Giô-suê", "gio-sue", "Joshua", "ヨシュア記"),
    BookSpec(7, "JDG", "OT", "cac", "Cac", "cacquanxet", "Judg", None, 21, "Các Quan Xét", "cac-quan-xet", "Judges", "士師記"),
    BookSpec(8, "RUT", "OT", "ru", "Ru", "ruto", "Ruth", None, 4, "Ru-tơ", "ru-to", "Ruth", "ルツ記"),
    BookSpec(9, "1SA", "OT", "1sa", "1Sa", "1samuen", "1Sam", None, 31, "I Sa-mu-ên", "1-sa-mu-en", "1 Samuel", "サムエル記上"),
    BookSpec(10, "2SA", "OT", "2sa", "2Sa", "2samuen", "2Sam", None, 24, "II Sa-mu-ên", "2-sa-mu-en", "2 Samuel", "サムエル記下"),
    BookSpec(11, "1KI", "OT", "1vua", "1Vua", "1cacvua", "1Kgs", None, 22, "I Các Vua", "1-cac-vua", "1 Kings", "列王紀上"),
    BookSpec(12, "2KI", "OT", "2vua", "2Vua", "2cacvua", "2Kgs", None, 25, "II Các Vua", "2-cac-vua", "2 Kings", "列王紀下"),
    BookSpec(13, "1CH", "OT", "1su", "1Su", "1suky", "1Chr", None, 29, "I Sử-ký", "1-su-ky", "1 Chronicles", "歴代志上"),
    BookSpec(14, "2CH", "OT", "2su", "2Su", "2suky", "2Chr", None, 36, "II Sử-ký", "2-su-ky", "2 Chronicles", "歴代志下"),
    BookSpec(15, "EZR", "OT", "exo", "Exo", "exora", "Ezra", None, 10, "Ê-xơ-ra", "e-xo-ra", "Ezra", "エズラ記"),
    BookSpec(16, "NEH", "OT", "ne", "Ne", "nehemi", "Neh", None, 13, "Nê-hê-mi", "ne-he-mi", "Nehemiah", "ネヘミヤ記"),
    BookSpec(17, "EST", "OT", "et", "Et", "exote", "Esth", None, 10, "Ê-xơ-tê", "e-xo-te", "Esther", "エステル記"),
    BookSpec(18, "JOB", "OT", "giop", "Giop", "giop", "Job", None, 42, "Gióp", "giop", "Job", "ヨブ記"),
    BookSpec(19, "PSA", "OT", "thi", "Thi", "thithien", "Ps", None, 150, "Thi-thiên", "thi-thien", "Psalms", "詩篇"),
    BookSpec(20, "PRO", "OT", "ch", "Ch", "chamngon", "Prov", None, 31, "Châm-ngôn", "cham-ngon", "Proverbs", "箴言"),
    BookSpec(21, "ECC", "OT", "tr", "Tr", "truyendao", "Eccl", None, 12, "Truyền-đạo", "truyen-dao", "Ecclesiastes", "伝道の書"),
    BookSpec(22, "SNG", "OT", "nha", "Nha", "nhaca", "Song", None, 8, "Nhã-ca", "nha-ca", "Song of Solomon", "雅歌"),
    BookSpec(23, "ISA", "OT", "es", "Es", "esai", "Isa", None, 66, "Ê-sai", "e-sai", "Isaiah", "イザヤ書"),
    BookSpec(24, "JER", "OT", "gie", "Gie", "gieremi", "Jer", None, 52, "Giê-rê-mi", "gie-re-mi", "Jeremiah", "エレミヤ書"),
    BookSpec(25, "LAM", "OT", "ca", "Ca", "cathuong", "Lam", None, 5, "Ca-thương", "ca-thuong", "Lamentations", "哀歌"),
    BookSpec(26, "EZK", "OT", "exe", "Exe", "exechien", "Ezek", None, 48, "Ê-xê-chi-ên", "e-xe-chi-en", "Ezekiel", "エゼキエル書"),
    BookSpec(27, "DAN", "OT", "da", "Da", "danien", "Dan", None, 12, "Đa-ni-ên", "da-ni-en", "Daniel", "ダニエル書"),
    BookSpec(28, "HOS", "OT", "os", "Os", "ose", "Hos", None, 14, "Ô-sê", "o-se", "Hosea", "ホセア書"),
    BookSpec(29, "JOL", "OT", "gio", "Gio", "gioen", "Joel", None, 3, "Giô-ên", "gio-en", "Joel", "ヨエル書"),
    BookSpec(30, "AMO", "OT", "am", "Am", "amot", "Amos", None, 9, "A-mốt", "a-mot", "Amos", "アモス書"),
    BookSpec(31, "OBA", "OT", "ap", "Ap", "apdia", "Obad", None, 1, "Áp-đia", "ap-dia", "Obadiah", "オバデヤ書"),
    BookSpec(32, "JON", "OT", "gion", "Gion", "giona", "Jonah", None, 4, "Giô-na", "gio-na", "Jonah", "ヨナ書"),
    BookSpec(33, "MIC", "OT", "mi", "Mi", "miche", "Mic", None, 7, "Mi-chê", "mi-che", "Micah", "ミカ書"),
    BookSpec(34, "NAM", "OT", "na", "Na", "nahum", "Nah", None, 3, "Na-hum", "na-hum", "Nahum", "ナホム書"),
    BookSpec(35, "HAB", "OT", "ha", "Ha", "habacuc", "Hab", None, 3, "Ha-ba-cúc", "ha-ba-cuc", "Habakkuk", "ハバクク書"),
    BookSpec(36, "ZEP", "OT", "so", "So", "sophoni", "Zeph", None, 3, "Sô-phô-ni", "so-pho-ni", "Zephaniah", "ゼパニヤ書"),
    BookSpec(37, "HAG", "OT", "ag", "Ag", "aghe", "Hag", None, 2, "A-ghê", "a-ghe", "Haggai", "ハガイ書"),
    BookSpec(38, "ZEC", "OT", "xa", "Xa", "xachari", "Zech", None, 14, "Xa-cha-ri", "xa-cha-ri", "Zechariah", "ゼカリヤ書"),
    BookSpec(39, "MAL", "OT", "ma", "Ma", "malachi", "Mal", None, 4, "Ma-la-chi", "ma-la-chi", "Malachi", "マラキ書"),
    # --- TÂN ƯỚC (27 SÁCH - 260 CHƯƠNG) ---
    BookSpec(40, "MAT", "NT", "mat", "Mat", "mathio", None, "61-Mt", 28, "Ma-thi-ơ", "ma-thi-o", "Matthew", "マタイによる福音書"),
    BookSpec(41, "MRK", "NT", "mac", "Mac", "mac", None, "62-Mk", 16, "Mác", "mac", "Mark", "マルコによる福音書"),
    BookSpec(42, "LUK", "NT", "lu", "Lu", "luca", None, "63-Lk", 24, "Lu-ca", "lu-ca", "Luke", "ルカによる福音書"),
    BookSpec(43, "JHN", "NT", "gi", "Gi", "giang", None, "64-Jn", 21, "Giăng", "giang", "John", "ヨハネによる福音書"),
    BookSpec(44, "ACT", "NT", "cong", "Cong", "congvucacsudo", None, "65-Ac", 28, "Công-vụ các Sứ-đồ", "cong-vu-cac-su-do", "Acts", "使徒行伝"),
    BookSpec(45, "ROM", "NT", "ro", "Ro", "roma", None, "66-Ro", 16, "Rô-ma", "ro-ma", "Romans", "ローマ人への手紙"),
    BookSpec(46, "1CO", "NT", "1co", "1Co", "1corinhto", None, "67-1Co", 16, "I Cô-rinh-tô", "1-co-rinh-to", "1 Corinthians", "コリント人への第一の手紙"),
    BookSpec(47, "2CO", "NT", "2co", "2Co", "2corinhto", None, "68-2Co", 13, "II Cô-rinh-tô", "2-co-rinh-to", "2 Corinthians", "コリント人への第二の手紙"),
    BookSpec(48, "GAL", "NT", "ga", "Ga", "galati", None, "69-Ga", 6, "Ga-la-ti", "ga-la-ti", "Galatians", "ガラテヤ人への手紙"),
    BookSpec(49, "EPH", "NT", "eph", "Eph", "epheso", None, "70-Eph", 6, "Ê-phê-sô", "e-phe-so", "Ephesians", "エペソ人への手紙"),
    BookSpec(50, "PHP", "NT", "phi", "Phi", "philip", None, "71-Php", 4, "Phi-líp", "phi-lip", "Philippians", "ピリピ人への手紙"),
    BookSpec(51, "COL", "NT", "co", "Co", "colose", None, "72-Col", 4, "Cô-lô-se", "co-lo-se", "Colossians", "コロサイ人への手紙"),
    BookSpec(52, "1TH", "NT", "1te", "1Te", "1tesalonica", None, "73-1Th", 5, "I Tê-sa-lô-ni-ca", "1-te-sa-lo-ni-ca", "1 Thessalonians", "テサロニケ人への第一の手紙"),
    BookSpec(53, "2TH", "NT", "2te", "2Te", "2tesalonica", None, "74-2Th", 3, "II Tê-sa-lô-ni-ca", "2-te-sa-lo-ni-ca", "2 Thessalonians", "テサロニケ人への第二の手紙"),
    BookSpec(54, "1TI", "NT", "1ti", "1Ti", "1timothe", None, "75-1Ti", 6, "I Ti-mô-thê", "1-ti-mo-the", "1 Timothy", "テモテへの第一の手紙"),
    BookSpec(55, "2TI", "NT", "2ti", "2Ti", "2timothe", None, "76-2Ti", 4, "II Ti-mô-thê", "2-ti-mo-the", "2 Timothy", "テモテへの第二の手紙"),
    BookSpec(56, "TIT", "NT", "tit", "Tit", "tit", None, "77-Tit", 3, "Tít", "tit", "Titus", "テトスへの手紙"),
    BookSpec(57, "PHM", "NT", "phil", "Phil", "philemon", None, "78-Phm", 1, "Phi-lê-môn", "phi-le-mon", "Philemon", "ピレモンへの手紙"),
    BookSpec(58, "HEB", "NT", "he", "He", "heboro", None, "79-Heb", 13, "Hê-bơ-rơ", "he-bo-ro", "Hebrews", "ヘブル人への手紙"),
    BookSpec(59, "JAS", "NT", "gia", "Gia", "giaco", None, "80-Jas", 5, "Gia-cơ", "gia-co", "James", "ヤコブの手紙"),
    BookSpec(60, "1PE", "NT", "1phi", "1Phi", "1phiero", None, "81-1Pe", 5, "I Phi-e-rơ", "1-phi-e-ro", "1 Peter", "ペテロの第一の手紙"),
    BookSpec(61, "2PE", "NT", "2phi", "2Phi", "2phiero", None, "82-2Pe", 3, "II Phi-e-rơ", "2-phi-e-ro", "2 Peter", "ペテロの第二の手紙"),
    BookSpec(62, "1JN", "NT", "1gi", "1Gi", "1giang", None, "83-1Jn", 5, "I Giăng", "1-giang", "1 John", "ヨハネの第一の手紙"),
    BookSpec(63, "2JN", "NT", "2gi", "2Gi", "2giang", None, "84-2Jn", 1, "II Giăng", "2-giang", "2 John", "ヨハネの第二の手紙"),
    BookSpec(64, "3JN", "NT", "3gi", "3Gi", "3giang", None, "85-3Jn", 1, "III Giăng", "3-giang", "3 John", "ヨハネの第三の手紙"),
    BookSpec(65, "JUD", "NT", "giu", "Giu", "giude", None, "86-Jud", 1, "Giu-đe", "giu-de", "Jude", "ユダの手紙"),
    BookSpec(66, "REV", "NT", "kh", "Kh", "khaihuyen", None, "87-Re", 22, "Khải-huyền", "khai-huyen", "Revelation", "ヨハネの黙示録"),
]

# Tổng số chương toàn Kinh Thánh chuẩn xác = 1.189
TOTAL_BIBLE_CHAPTERS = sum(b.chapters for b in BIBLE_BOOKS_66)
assert len(BIBLE_BOOKS_66) == 66, f"Expected 66 books, got {len(BIBLE_BOOKS_66)}"
assert TOTAL_BIBLE_CHAPTERS == 1189, f"Expected 1189 chapters, got {TOTAL_BIBLE_CHAPTERS}"

# Các bảng tra cứu O(1)
BY_USFM: Dict[str, BookSpec] = {b.usfm: b for b in BIBLE_BOOKS_66}
BY_HTTLVN_CODE: Dict[str, BookSpec] = {b.httlvn_code: b for b in BIBLE_BOOKS_66}
BY_TINLANH_SLUG: Dict[str, BookSpec] = {b.tinlanh_slug: b for b in BIBLE_BOOKS_66}
BY_BOOK_NR: Dict[int, BookSpec] = {b.book_nr: b for b in BIBLE_BOOKS_66}
BY_WLC_OSIS: Dict[str, BookSpec] = {b.wlc_osis: b for b in BIBLE_BOOKS_66 if b.wlc_osis}

# Bảng tra cứu viết tắt tham chiếu chéo (TRAP A3) -> USFM
CROSSREF_ABBR_TO_USFM: Dict[str, str] = {
    b.httlvn_code.lower(): b.usfm for b in BIBLE_BOOKS_66
}
CROSSREF_ABBR_TO_USFM.update({
    b.crossref_abbr.lower(): b.usfm for b in BIBLE_BOOKS_66
})
# Các biến thể viết tắt phụ có thể xuất hiện trong chú thích hoặc data-bible
CROSSREF_ABBR_TO_USFM.update({
    "exr": "EZR",
    "ext": "EST",
    "cham": "PRO",
    "ho": "HOS",
    "phim": "PHM",
    "khai": "REV",
    "sang": "GEN",
    "xuat": "EXO",
    "phuc": "DEU",
    "quan": "JDG",
    "vua1": "1KI",
    "vua2": "2KI",
    "su1": "1CH",
    "su2": "2CH",
    "thithien": "PSA",
    "tt": "PSA",
    "cn": "PRO",
    "td": "ECC",
    "mat-thi-o": "MAT",
    "giang": "JHN",
    "cong-vu": "ACT",
})


def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt (phục vụ so khớp tên sách/tìm kiếm không dấu)."""
    text = text.replace("Đ", "D").replace("đ", "d").replace("\u00d0", "D").replace("\u00f0", "d")
    nfd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def resolve_book(identifier: str) -> Optional[BookSpec]:
    """
    Giải mã linh hoạt bất kỳ mã sách, tên sách (có dấu/không dấu) hoặc viết tắt nào
    về đúng đối tượng `BookSpec`.
    """
    if not identifier:
        return None
    clean = identifier.strip()
    upper = clean.upper()
    if upper in BY_USFM:
        return BY_USFM[upper]

    lower = clean.lower()
    if lower in BY_HTTLVN_CODE:
        return BY_HTTLVN_CODE[lower]
    if lower in CROSSREF_ABBR_TO_USFM:
        return BY_USFM[CROSSREF_ABBR_TO_USFM[lower]]
    if lower in BY_TINLANH_SLUG:
        return BY_TINLANH_SLUG[lower]

    # Thử khớp theo slug không dấu
    slug_candidate = re.sub(r"[^a-z0-9]+", "", strip_accents(lower))
    if slug_candidate in BY_TINLANH_SLUG:
        return BY_TINLANH_SLUG[slug_candidate]

    for b in BIBLE_BOOKS_66:
        if strip_accents(b.name_vi_1925).lower() == strip_accents(clean).lower():
            return b
        if b.slug_vi.replace("-", "") == slug_candidate:
            return b
    return None

