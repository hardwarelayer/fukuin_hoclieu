# `vietchristian.com` — Cổng Tư Liệu Cơ Đốc Tiếng Việt (Enrichment & Cross-Reference Oracle)

* **Source ID**: `vietchristian`
* **Trang gốc**: `https://vietchristian.com`
* **Ngày khảo sát & Reverse Engineering**: 08/11/2026
* **Vai trò trong hệ sinh thái `fukuin_hoclieu`**: Nguồn làm giàu dữ liệu (Enrichment Source) và đối chiếu chéo độc lập cho 7 hạng mục:
  1. **Lời 511 Bài Thánh Ca Truyền Thống Dạng Text Phẳng** (`/thanhca/thanhca.txt` — `466.5 KB`) để đối chiếu chéo với `thanhca.httlvn.org`.
  2. **Bảng Ánh Xạ Số Bài Thánh Ca 2 Hệ Phái + Tên Tiếng Anh Gốc** (`POST /thanhca/result.asp` với `hid=0` và `hid=1`).
  3. **70 Bài Kinh Thánh Đối Đáp Truyền Thống Dạng Text Phẳng** (`/thanhca/ktdd.txt` — `142.0 KB`).
  4. **Bảng Câu Gốc Dưỡng Linh Theo Tâm Trạng / Nhu Cầu Tâm Linh** (`/kinhthanh/` `#divDL`).
  5. **Lịch Niên Giám Ngày Lễ Cơ Đốc Hàng Năm** (`/event/`).
  6. **Lịch Đọc Kinh Thánh 4 Lộ Trình** (`/kinhthanh/dbr.asp`) & **Cơ chế Đố Kinh Thánh Base64** (`/kinhthanh/quizMain.asp`).
  7. **Thánh Kinh Lược Khảo** (`/kinhthanh/tklk/tklk.xml` + `.dat` — tư liệu tham khảo nội bộ khi biên soạn phần giới thiệu sách).

---

## 1. Hạ Tầng Server, Cloudflare `jsd` & Chiến Lược "Zero-Flood" (Chỉ ~10 Request Tĩnh)

### 1.1. Phân tích lớp bảo vệ Cloudflare
* **Web Server**: Classic ASP (`.asp`) trên IIS, đứng sau **Cloudflare Proxy (`CF-RAY` có mặt trên mọi response)**.
* **Cloudflare JS Detection (`jsd`)**: Cuối mỗi trang HTML có chèn đoạn script `/cdn-cgi/challenge-platform/scripts/jsd/main.js`.
* **Quy tắc chống chặn (Anti-blocking Policy)**:
  - Ở tốc độ tuần tự (`delay >= 2.0s / request`) kèm `User-Agent` trình duyệt chuẩn, Cloudflare cho phép đi qua thẳng (`HTTP 200 OK`) mà không bật CAPTCHA/Turnstile.
  - **Đặc biệt quan trọng**: Nhờ phát hiện ra hệ thống file phẳng (`.txt`, `.xml`) và cú pháp truy vấn toàn bảng (`Searchtype=index`) của `vietchristian.com`, **toàn bộ dữ liệu cần thiết trên `vietchristian.com` chỉ tốn đúng 7–10 HTTP requests** (thay vì hàng ngàn request lẻ)! Tuyệt đối không bao giờ chạy vòng lặp quét từng bài hát hay từng câu đố trên `vietchristian.com`.

### 1.2. Bảng tổng hợp các Endpoint Chiến Lược

| STT | Tài nguyên | Phương thức & URL | Kích thước thực tế | Vai trò khai thác |
|---|---|---|---|---|
| 1 | Toàn văn 511 bài Thánh Ca | `GET https://vietchristian.com/thanhca/thanhca.txt` | `466,535 bytes` | Đối chiếu chéo lời của 511 bài Thánh Ca đầu với `thanhca.httlvn.org` |
| 2 | Toàn văn 70 bài KTĐĐ | `GET https://vietchristian.com/thanhca/ktdd.txt` | `142,055 bytes` | Đối chiếu chéo 70 bài Kinh Thánh Đối Đáp đầu với `thanhca.httlvn.org` |
| 3 | Danh mục Thánh Ca `hid=0` | `POST https://vietchristian.com/thanhca/result.asp` (`vn=1&Searchtype=index&hid=0`) | `~243 KB` | Bảng tổng hợp 509 bài Thánh Ca Truyền Thống (kèm tên bài Tiếng Anh gốc & tác giả) |
| 4 | Danh mục Thánh Ca `hid=1` | `POST https://vietchristian.com/thanhca/result.asp` (`vn=1&Searchtype=index&hid=1`) | `~485 KB` | Bảng tổng hợp 511 bài Thánh Ca Tôn Vinh Chúa (HTTLVN Hoa Kỳ) kèm tên Tiếng Anh |
| 5 | Bảng Câu Gốc Dưỡng Linh | `GET https://vietchristian.com/kinhthanh/` | `~38 KB` | Bóc tách khối `<div id="divDL">` (ánh xạ Tâm trạng $\leftrightarrow$ Đoạn Kinh Thánh) |
| 6 | Lịch Ngày Lễ Cơ Đốc | `GET https://vietchristian.com/event/` | `~18 KB` | Bảng ngày lễ Cơ Đốc theo năm dương lịch (*Mùa Vọng, Giáng Sinh, Lễ Tro, Thương Khó, Phục Sinh, Ngũ Tuần...*) |
| 7 | Thánh Kinh Lược Khảo | `GET https://vietchristian.com/kinhthanh/tklk/tklk.xml` | `7,289 bytes` | Mục lục XML trỏ tới các file `.dat` khảo sát bối cảnh 66 sách (lưu nội bộ) |

---

## 2. Giải Phẫu Định Dạng Dữ Liệu & 4 "Bẫy Runtime" (TRAP D1, D2, D9, D10)

### 2.1. Bẫy D1 — Lỗi Mã Hóa Kép UTF-8 (Double-Encoded UTF-8 Mojibake) Trong `tklk.xml` và `.dat`
* **Hiện tượng thực nghiệm**: Khi tải `https://vietchristian.com/kinhthanh/tklk/tklk.xml`, dù phần đầu khai báo `<?xml version="1.0" encoding="utf-8"?>`, nội dung chuỗi bên trong bị biến dạng kiểu Mojibake:
  ```xml
  <book title="ThÃ¡nh Kinh LÆ°á»£c Kháº£o" code="00GioiThieu.dat">
    <chapter title="ChÆ°Æ¡ng I: CÃ¡ch PhÃ¢n Loáº¡i SÃ¡ch Trong ThÃ¡nh Kinh" />
  ```
* **Nguyên nhân gốc rễ**: Dữ liệu gốc ban đầu đã là chuỗi byte UTF-8, nhưng công cụ biên tập cũ mở file đó theo bảng mã **Windows-1252 (`cp1252`)** rồi lại lưu xuất ra UTF-8 một lần nữa (Double UTF-8 Encoding).
* **Hàm khôi phục chính xác 100% (`fix_double_utf8`)**:
  ```python
  def fix_double_utf8(corrupted_text: str) -> str:
      """
      Khôi phục chuỗi UTF-8 bị mã hóa kép qua bảng mã Windows-1252 (cp1252).
      Ví dụ: 'ThÃ¡nh Kinh LÆ°á»£c Kháº£o' -> 'Thánh Kinh Lược Khảo'
      """
      try:
          return corrupted_text.encode("cp1252").decode("utf-8")
      except (UnicodeEncodeError, UnicodeDecodeError):
          # Nếu chuỗi có pha trộn ký tự không thuộc cp1252, khôi phục từng từ/đoạn
          import re
          def _repair_chunk(m):
              chunk = m.group(0)
              try:
                  return chunk.encode("cp1252").decode("utf-8")
              except Exception:
                  return chunk
          return re.sub(r"[\x80-\xff\u0100-\u203a]+", _repair_chunk, corrupted_text)
  ```
  Đã kiểm thử trực tiếp: `'ThÃ¡nh Kinh LÆ°á»£c Kháº£o'.encode('cp1252').decode('utf-8')` trả về chính xác `'Thánh Kinh Lược Khảo'`!

### 2.2. Bẫy D2 — Ký Tự `Ð` (`U+00D0` Eth) & Giới Hạn 70 Bài Trong `/thanhca/ktdd.txt`
* **Hiện tượng thực nghiệm**:
  1. File `https://vietchristian.com/thanhca/ktdd.txt` (`142,055 bytes`) chỉ chứa **70 bài Kinh Thánh Đối Đáp** (`Bài 1` đến `Bài 70` theo ấn bản cũ), trong khi `thanhca.httlvn.org/kinh-thanh-doi-dap` có đầy đủ **100 bài** (`001` đến `100`).
  2. Toàn bộ chữ `Đ` hoa tiếng Việt trong `ktdd.txt` và `thanhca.txt` đều bị lưu bằng ký tự **`Ð` (`U+00D0` — Latin Capital Letter Eth)**:
     ```text
     Bài 1: ÐẤNG TẠO HÓA
     (Sáng-thế Ký 1:1-6; Ê-sai 40:12-28)
     Ban đầu Ðức Chúa Trời dựng nên trời đất.
     ```
* **Quy tắc xử lý bắt buộc**:
  - Chạy `.replace("\u00d0", "\u0110").replace("\u00f0", "\u0111")` và `unicodedata.normalize("NFC", text)` ngay khi đọc `ktdd.txt` và `thanhca.txt`.
  - Dùng `thanhca.httlvn.org` làm nguồn chính cho đủ 100 bài KTĐĐ, và dùng `ktdd.txt` để đối chiếu chéo nội dung 70 bài đầu tiên.

### 2.3. Bẫy D9 — Cấu Trúc Văn Bản Phẳng Của `/thanhca/thanhca.txt` (511 Bài)
* Kiểm thử trực tiếp `https://vietchristian.com/thanhca/thanhca.txt` (`466,535 bytes`):
  - Chứa toàn văn lời của **511 bài Thánh Ca Truyền Thống**.
  - Các bài phân cách nhau bởi dòng tiêu đề hoặc thẻ phân đoạn trong `reader.asp`.
  - Đây là nguồn đối chiếu (Oracle) cực quý để kiểm tra xem 511 bài đầu trên `thanhca.httlvn.org` có bị lỗi mất dòng hoặc dính chữ khi bóc thẻ `<i class="chord-group">` hay không.

### 2.4. Bẫy D10 — Lấy Trọn Bộ Bảng Ánh Xạ Thánh Ca Việt – Anh Bằng 2 Lệnh `POST /thanhca/result.asp`
* Thay vì gửi hàng trăm request tìm kiếm, form tại `/thanhca/result.asp` chấp nhận payload:
  - `vn=1&Searchtype=index&hid=0` (`~243 KB`): Trả về bảng HTML chứa toàn bộ **509 bài Thánh Ca Truyền Thống**.
  - `vn=1&Searchtype=index&hid=1` (`~485 KB`): Trả về bảng HTML chứa toàn bộ **511 bài Thánh Ca Tôn Vinh Chúa (`HTTLVN Hoa Kỳ`)**.
* **Giá trị đặc biệt của bảng `result.asp`**:
  - Cung cấp **Tên bài Thánh Ca bằng tiếng Anh nguyên gốc (Original English Title)** (ví dụ Bài 1 *Cúi Xin Vua Thánh Ngự Lai* $\leftrightarrow$ *Come, Thou Almighty King*; Bài 42 *Lớn Bấy Duy Ngài* $\leftrightarrow$ *How Great Thou Art*).
  - Nhờ trường `original_english_title` và tên tác giả nhạc (`composer`), bộ đối sánh trong `fukuin_hoclieu` có thể **tự động liên kết chéo (Cross-link)** giữa bài Thánh Ca tiếng Việt (`VI_TC`) và bài Thánh Ca tiếng Nhật tương ứng trong **`Sanbika 1954` (`JA_SANBIKA`)**!

---

## 3. Giải Mã Cơ Chế Đố Kinh Thánh Base64 (`quizMain.asp`) & Bảng Dưỡng Linh (`#divDL`)

### 3.1. Giải mã `POST /kinhthanh/quizMain.asp`
* Khi gửi `POST https://vietchristian.com/kinhthanh/quizMain.asp` với body `TestLevel=2&BookVersion=1934`:
  - Server trả về ngẫu nhiên 1 câu Kinh Thánh trong `<input type="hidden" name="BibleVerse" value="..." />`.
  - Đáp án đúng được giấu trong `<input type="hidden" name="id" value="RMOibi1z4buRIEvDvSAxMTo3IHwzfDMmMTE6Nw" />`.
  - Khi thêm padding `=` và giải mã Base64 (`base64.b64decode(val + "==").decode("utf-8")`), chuỗi thu được là:
    `Dân-số Ký 11:7 |3|3&11:7` (gồm `Tên Sách đoạn:câu | TestLevel | BookIndex&Chapter:Verse`).
* **Quyết định thiết kế**: Vì `quizMain.asp` chỉ bốc ngẫu nhiên câu Kinh Thánh từ bản 1934 để hỏi địa chỉ sách/đoạn, ta **không crawl `quizMain.asp`**, mà tự sinh ngân hàng câu hỏi trắc nghiệm tĩnh (`quizzes/`) trực tiếp từ kho JSON Bản 1925 sạch của `fukuin_hoclieu`.

### 3.2. Bóc tách Bảng Câu Gốc Dưỡng Linh (`#divDL` trên `/kinhthanh/`)
* Trong trang `/kinhthanh/`, khối `<div id="divDL">` chứa danh sách các chủ đề tâm trạng / nhu cầu tâm linh gắn với địa chỉ Kinh Thánh (ví dụ *Khi buồn rầu* $\rightarrow$ `Giăng 14`, `Thi-thiên 46`; *Cô đơn hay sợ hãi* $\rightarrow$ `Thi-thiên 23`; *Lo lắng* $\rightarrow$ `Ma-thi-ơ 6:19-34`...).
* Bộ parser `parse_vietchristian_duong_linh()` trích xuất bảng này thành file `quotes/mood-scripture-seeds.json` để làm hạt giống cho hệ thống **Daily Quotes & Trang Trích Dẫn Theo Tâm Trạng**.

---

## 4. Quy Trình Pipeline 3 Bước & Quản Lý Trạng Thái (`state/vietchristian_state.json`)

* `--step 1` (**Fetch Bulk Static & Index Files — 7 Requests**):
  - Tải tuần tự với delay `2.5s` giữa các request:
    1. `GET /thanhca/thanhca.txt` $\rightarrow$ `raw/vietchristian/thanhca.txt`
    2. `GET /thanhca/ktdd.txt` $\rightarrow$ `raw/vietchristian/ktdd.txt`
    3. `POST /thanhca/result.asp` (`hid=0`) $\rightarrow$ `raw/vietchristian/hymn_index_hid0.html`
    4. `POST /thanhca/result.asp` (`hid=1`) $\rightarrow$ `raw/vietchristian/hymn_index_hid1.html`
    5. `GET /kinhthanh/` $\rightarrow$ `raw/vietchristian/kinhthanh_home.html`
    6. `GET /event/` $\rightarrow$ `raw/vietchristian/events.html`
    7. `GET /kinhthanh/tklk/tklk.xml` $\rightarrow$ `raw/vietchristian/tklk.xml`
* `--step 2` (**Repair Encoding & Parse**):
  - Áp dụng `normalize_vietnamese_1925()` (sửa `Ð` $\to$ `Đ`) cho `thanhca.txt` và `ktdd.txt`.
  - Áp dụng `fix_double_utf8()` cho `tklk.xml`.
  - Bóc tách bảng ánh xạ tên tiếng Anh bài Thánh Ca từ `hymn_index_hid0.html` và `hymn_index_hid1.html`.
* `--step 3` (**Cross-Link & Enrich**):
  - Ghép tên tiếng Anh gốc (`original_title_en`) vào 903 bài Thánh Ca trong `hymns/vi-thanh-ca/` và đối chiếu chéo lời 511 bài đầu + 70 bài KTĐĐ đầu.
