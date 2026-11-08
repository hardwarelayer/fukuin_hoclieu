# `fukuin_hoclieu` — Kho Ngữ Liệu & Học Liệu Số Kinh Thánh, Thánh Ca Đa Ngữ (Việt – Anh – Nhật – Nguyên Bản)

Hệ thống kho ngữ liệu và học liệu số có cấu trúc đồ thị hai chiều toàn diện, phục vụ nền tảng web tĩnh miễn phí **[fukuin](../fukuin/README.md)** (Kinh Thánh, Thánh Ca, Kinh Thánh Đối Đáp, Lịch sử Hội Thánh & Học ngoại ngữ qua Kinh Thánh).

Toàn bộ dữ liệu được thu thập, đối chiếu chéo đa nguồn (3-Way Majority Voting) và chuẩn hóa nghiêm ngặt theo ranh giới **100% Public Domain / Open License**, kế thừa trực tiếp kiến trúc của [RoTK9_hoclieu](../RoTK9_hoclieu/README.md) và [LumiLearnWeb_hoclieu](../LumiLearnWeb_hoclieu/docs/README.md).

> 📌 **Điểm vào tài liệu bắt buộc cho đội dự án**:
> - **[docs/SoT.md](./docs/SoT.md)** — *Single Source of Truth*: Kiến trúc dữ liệu tổng thể, đồ thị liên kết 2 chiều và lộ trình 4 giai đoạn.
> - **[crawl_factory/README.md](./crawl_factory/README.md)** — *Sổ tay Vận hành Crawler*: Hướng dẫn chạy CLI `run_crawler.py`, cơ chế tạm dừng `Ctrl+C` / `Resume` và quy trình build.
> - **[crawl_factory/sources/docs/technical-design-and-anti-blocking.md](./crawl_factory/sources/docs/technical-design-and-anti-blocking.md)** — *Ma trận 18 Bẫy Runtime (`TRAP A1` – `TRAP E1`)* bắt buộc phải nắm trước khi sửa code parser.

---

## 🌟 Điểm Nhấn Kỹ Thuật & Xử Lý 18 Bẫy Runtime

1. **Hội đồng Đối chiếu Ba Nguồn Độc lập (3-Way Majority Voting) cho Kinh Thánh Bản Truyền Thống 1925 (`VI1934`)**:
   - Kết hợp `kinhthanh.httlvn.org` (Primary) + `www.tinlanh.com` (`.shtml` Secondary) + `GetBible vietnamese.json` (Tertiary) để tự động loại bỏ lỗi gạch nối OCR (`Đức-Giê hô-va` tại `thithien23.shtml`) và chuẩn hóa ký tự `Ð` (`U+00D0` Eth) về `Đ` (`U+0110`).
   - Bóc tách cú pháp kép `][gt=` trong thẻ `<a title="...">⚓</a>` để khôi phục đầy đủ **16 câu Tân Ước bị lược trong bản Critical Text** (`Ma-thi-ơ 17:21`...) kèm ghi chú văn bản học.
2. **Căn chỉnh Đa ngôn ngữ 6 Phiên bản (Việt – Anh – Nhật – Nguyên bản Hê-bơ-rơ / Hy Lạp)**:
   - **Tiếng Việt**: Bản Truyền Thống 1925 (`VI1934`).
   - **Tiếng Anh**: `World English Bible (WEB)` (hiện đại, dễ hiểu) + `King James Version (KJV)` (cổ điển, gắn mã số Strong `Hxxxx`/`Gxxxx` chuẩn xác).
   - **Tiếng Nhật**: `口語訳聖書 (Kougo-yaku 1955)` (đã bóc tách sẵn Furigana `<ruby>神<rt>かみ</rt></ruby>` từ `Bolls.life JPKJV.json` và sửa bẫy lệch số câu `+1/+2` do thượng đề `[0]`/`[00]` ở sách Thi-thiên) + `文語訳聖書 (Bungo-yaku 1917)`.
   - **Nguyên bản**: Cựu Ước Hê-bơ-rơ (`Westminster Leningrad Codex - WLC`, xử lý `lemma="c/d/776"`, `"1254 a"` và xóa dấu `/` hình thái học) + Tân Ước Hy Lạp (`MorphGNT SBLGNT`).
3. **Chiến lược Giảm 78% Request khi Thu thập 903 Bài Thánh Ca & 100 Bài Kinh Thánh Đối Đáp**:
   - Hợp nhất tab `Lời` và `Hợp âm` (`?op=chords`) chỉ trong 1 request/bài, xử lý cả 2 họ DOM lời hát và bẫy hợp âm nằm giữa từ ghép có gạch nối (`Giê-[Eb]ru-sa-lem`).
   - Trích xuất trọn bộ danh sách **384 bài có Nhạc MP3** chỉ bằng 1 request duy nhất từ `#audio-player-playlist`.
4. **Kiểm thử Tự động 100% (`tools/validate_hoclieu.py`)**:
   - Kiểm tra tự động toàn bộ 66 sách (`1.189` chương), bảng lệnh tắt buổi nhóm (`worship_aliases.json`), và 18 điều kiện bất biến của dữ liệu trước khi xuất sang web app `fukuin`.

---

## 🚀 Hướng Dẫn Nhanh Cho Lập Trình Viên (Quick Start)

### 1. Yêu cầu môi trường
- **Python 3.9+** (khuyến nghị Python 3.11+).
- **0 phụ thuộc bên ngoài (Zero External Dependencies)**: Toàn bộ khung `crawl_factory/` và `tools/` chỉ sử dụng thư viện chuẩn của Python (`urllib`, `json`, `re`, `unicodedata`, `hashlib`, `signal`, `pathlib`).

### 2. Chạy Kiểm thử Mẫu (Smoke Test)
```powershell
cd C:\HomeWorking\911\repos\fukuin_hoclieu

# Tải & phân tích thử các chương có Bẫy Runtime điển hình (MAT 17, PSA 51, PSA 23) + 2 bài Thánh Ca
python -X utf8 crawl_factory\run_crawler.py --source kinhthanh_httlvn --step all --book MAT --chapter 17
python -X utf8 crawl_factory\run_crawler.py --source kinhthanh_httlvn --step all --book PSA --chapter 51
python -X utf8 crawl_factory\run_crawler.py --source tinlanh_com --step all --book PSA --chapter 23
python -X utf8 crawl_factory\run_crawler.py --source open_multilingual --step all --book PSA --chapter 51
python -X utf8 crawl_factory\run_crawler.py --source thanhca_httlvn --step all --limit 2

# Tổng hợp sang thư mục data/ và chạy Quality Gate kiểm định
python -X utf8 tools\build_hoclieu.py
python -X utf8 tools\validate_hoclieu.py
```

---

## 📂 Cấu Trúc Thư Mục Toàn Dự Án

- **[docs/](./docs/)**: Tài liệu kiến trúc dữ liệu, chính sách bản quyền, schema JSON, 60 câu chuyện Kinh Thánh minh họa bút chì và dữ liệu bản đồ Hội Thánh VN/JP.
- **[crawl_factory/](./crawl_factory/)**: Nhà máy thu thập dữ liệu đa nguồn (`core/`, `sources/`, `state/`, `raw/`, `normalized/`).
- **[tools/](./tools/)**: Các công cụ chưng cất (`build_hoclieu.py`) và kiểm định toàn vẹn 2 chiều (`validate_hoclieu.py`).
- **[data/](./data/)**: Kho dữ liệu JSON hoàn chỉnh sẵn sàng cung cấp cho ứng dụng web `fukuin`.

