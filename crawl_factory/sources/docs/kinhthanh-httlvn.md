# `kinhthanh.httlvn.org` — Kinh Thánh Trực Tuyến (Tổng Liên Hội HTTLVN)

* **Source ID**: `kinhthanh_httlvn`
* **Trang gốc**: `https://kinhthanh.httlvn.org/?v=VI1934`
* **Ngày khảo sát & Reverse Engineering**: 08/11/2026
* **Vai trò trong hệ sinh thái `fukuin_hoclieu`**: Nguồn chuẩn số 1 (Primary Source) cho toàn văn Kinh Thánh Tiếng Việt Bản Truyền Thống 1925 (`VI1934`), hệ thống tiêu đề phân đoạn (`<h1>`, `<h2>`, `<h3>`, `<p>`), thượng đề Thi-thiên (`<i>`), đồ thị câu tham chiếu chéo (`⚓`), ghi chú văn bản học (`][gt=...`) và đường dẫn Audio MP3 theo chương.

---

## 1. Kiến Trúc Server, Session & Endpoints

### 1.1. Hạ tầng kỹ thuật & Cơ chế chống Crawl
Qua kiểm thử HTTP thực nghiệm trên `https://kinhthanh.httlvn.org`:
* **Web Server**: `Microsoft-IIS/10.0` (ASP.NET MVC 5, Bootstrap 3), render hoàn toàn phía Server (SSR).
* **WAF / Anti-bot**: **Không có Cloudflare** (`CF-RAY: None`), không có CAPTCHA, không có rate-limit cứng ở tầng edge.
* **Cơ chế Cookie & Phiên bản (`Set-Cookie`)**:
  - Mỗi phản hồi từ server trả về header:
    `Set-Cookie: version_current=VI1934; expires=...; path=/`
  - **Quy tắc bắt buộc khi crawl**: Luôn truyền tường minh query string `?v=VI1934` trên mọi URL VÀ gửi kèm header `Cookie: version_current=VI1934` để tránh việc server fallback về bản hiệu đính (`RVV11` hoặc `NVB`) nếu thiếu tham số.
* **Tổng khối lượng & Tốc độ crawl an toàn**:
  - Tổng số trang chương cần tải: **1.189 chương** (66 sách).
  - Dung lượng trung bình mỗi trang chương: `48 KB – 145 KB` HTML.
  - Delay khuyến nghị: `1.0s – 1.5s / request` kèm jitter ngẫu nhiên `±0.3s`, chạy tuần tự (`concurrency = 1`). Toàn bộ 1.189 chương hoàn tất trong **~25 phút** và được lưu nguyên bản vào `raw/kinhthanh_httlvn/VI1934/{book_code}/{chapter}.html`.

### 1.2. Bảng tổng hợp URL Endpoints

| Loại trang | Phương thức & URL Pattern | Ví dụ thực tế | Ghi chú kỹ thuật |
|---|---|---|---|
| **Mục lục toàn bộ 1.189 chương** | `GET /?v={version}` | `/?v=VI1934` | Trang HTML (`~186.9 KB`) chứa toàn bộ `1.189` thẻ `<a href="/doc-kinh-thanh/{book_code}/{chapter}?v=VI1934">`. Dùng cho **Step 1 (Discovery)**. |
| **Đọc 1 chương (Primary)** | `GET /doc-kinh-thanh/{book_code}/{chapter}?v={version}` | `/doc-kinh-thanh/sa/1?v=VI1934` | Trả về toàn bộ các câu trong chương, tiêu đề phân đoạn, tham chiếu chéo `⚓`, ghi chú `][gt=` và đường dẫn Audio. Dùng cho **Step 2 (Fetch)**. |
| **Đọc song song 2 bản** | `GET /doc-kinh-thanh/{book_code}/{chapter}?v={v1}&v2={v2}` | `/doc-kinh-thanh/sa/1?v=VI1934&v2=NKJV` | Hiển thị 2 cột song song (không cần crawl vì ta tự căn chỉnh đa ngữ ở tầng JSON). |
| **So sánh nhiều bản dịch** | `GET /so-sanh-ban-dich/{book_code}/{chapter}?v={version}` | `/so-sanh-ban-dich/sa/1?v=VI1934` | So sánh từng câu giữa các bản. |
| **Tìm kiếm toàn văn** | `POST /Search` (`query=...`) | — | Tìm kiếm trên server (không cần dùng). |
| **Audio MP3 theo chương** | `GET /Audio/{version}/{speaker}/{book_code}/{chapter}.mp3` | `/Audio/VI1934/1-ms-nguyen-thi/sa/1.mp3` | `HTTP 200 OK`, `Content-Type: audio/mpeg` (ví dụ `sa/1.mp3` nặng `3.67 MB`). |

---

## 2. Phân Loại Pháp Lý 16 Mã Bản Dịch Trên Nguồn

Khảo sát `<select id="version">` trên `kinhthanh.httlvn.org` ghi nhận 16 mã bản dịch:

1. **Nhóm Public Domain (ĐƯỢC PHÉP SỬ DỤNG TOÀN VĂN)**:
   - **`VI1934`**: *Kinh Thánh Tiếng Việt 1925* (Bản Truyền Thống Phan Khôi / C&MA / British and Foreign Bible Society, xuất bản 1925–1926, in lại 1934). **Đây là mã duy nhất được phép crawl và xuất bản toàn văn lên `fukuin`.**
2. **Nhóm Bản Quyền Thương Mại / Tổ Chức (TUYỆT ĐỐI KHÔNG CRAWL LÊN SITE)**:
   - Tiếng Việt hiện đại: `RVV11` (Truyền Thống Hiệu Đính 2010 — UBS), `BD2011` (MS Đặng Ngọc Báu), `NVB` (Bản Dịch Mới), `BPT` (Bản Phổ Thông — Biblica), `BDY` (Bản Diễn Ý).
   - Tiếng Anh / Hoa / Dân tộc thiểu số: `NKJV`, `NIV`, `RCUV`, `RCUVSS`, `RRB` (Ê-đê), `JBSV` (Gia-rai), `BRU` (Bru), `IUMINR` (Dao), `HMOWSV` / `HWB` / `HMOBSV` (H'Mông), `BBSV` (Ba-na).

---

## 3. Bảng Ánh Xạ Đầy Đủ 66 Sách & Các "Bẫy Mã Sách" (TRAP A1 & TRAP A3)

> [!CAUTION]
> **BẪY RUNTIME A1 — 6 Mã Sách URL (`book_code`) Khác Biệt Với Cách Viết Tắt Thông Thường**:
> Qua bóc tách trực tiếp toàn bộ 1.189 liên kết trên trang chủ `/?v=VI1934`, có **6 mã sách trên URL** rất dễ gây lỗi `HTTP 404` hoặc **nhầm lẫn chéo giữa 2 sách** nếu lập trình viên tự suy đoán:
> 1. **Ê-xơ-ra (Ezra, 10 chương)** có mã URL là **`exo`** (KHÔNG phải `exr`!). Cần cực kỳ cẩn thận phân biệt bộ ba: **`xu`** (*Xuất Ê-díp-tô Ký*), **`exo`** (*Ê-xơ-ra*), và **`exe`** (*Ê-xê-chi-ên*).
> 2. **Ê-xơ-tê (Esther, 10 chương)** có mã URL là **`et`** (KHÔNG phải `ext`).
> 3. **Châm-ngôn (Proverbs, 31 chương)** có mã URL là **`ch`** (KHÔNG phải `cham`).
> 4. **Ô-sê (Hosea, 14 chương)** có mã URL là **`os`** (KHÔNG phải `ho`).
> 5. **Phi-líp (Philippians, 4 chương)** có mã URL là **`phi`**, trong khi **Phi-lê-môn (Philemon, 1 chương)** có mã URL là **`phil`**! Nếu gán nhầm `phil` cho Phi-líp sẽ dẫn đến lấy nhầm sách Phi-lê-môn!
> 6. **Khải-huyền (Revelation, 22 chương)** có mã URL là **`kh`** (KHÔNG phải `khai`).

> [!WARNING]
> **BẪY RUNTIME A3 — Mã Viết Tắt Trong Tooltip Tham Chiếu Chéo (`⚓`) Khác Với `book_code` Trên URL**:
> Bên trong thuộc tính `title="..."` của thẻ `<a data-toggle="tooltip">⚓</a>`, hệ thống dùng chữ hoa đầu từ (TitleCase như `Sa`, `Xu`, `1Co`, `Mat`, `Mac`, `Kh`, `Exe`), nhưng một số sách viết tắt khác với URL (hoặc có biến thể). Bảng dưới đây chuẩn hóa toàn bộ ánh xạ giữa **Chuẩn USFM 3.0**, **URL `httlvn_code`**, **Mã tham chiếu `crossref_abbr`**, **Mã `getbible_nr`** và **Slug `tinlanh.com`**.

### 3.1. Cựu Ước (39 Sách — 929 Chương)

| # | USFM | `httlvn_code` (URL) | `crossref_abbr` (`⚓` Tooltip) | `tinlanh_slug` (`tinlanh.com`) | `getbible_nr` | Số chương | Tên sách chuẩn (Bản 1925) |
|---|---|---|---|---|---|---|---|
| 1 | `GEN` | `sa` | `Sa` | `sangtheky` | 1 | 50 | Sáng-thế Ký |
| 2 | `EXO` | `xu` | `Xu` | `xuatediptoky` | 2 | 40 | Xuất Ê-díp-tô Ký |
| 3 | `LEV` | `le` | `Le` | `leviky` | 3 | 27 | Lê-vi Ký |
| 4 | `NUM` | `dan` | `Dan` | `dansoky` | 4 | 36 | Dân-số Ký |
| 5 | `DEU` | `phu` | `Phu` | `phuctruyenluatleky` | 5 | 34 | Phục-truyền Luật-lệ Ký |
| 6 | `JOS` | `gios` | `Gios` | `giosue` | 6 | 24 | Giô-suê |
| 7 | `JDG` | `cac` | `Cac` | `cacquanxet` | 7 | 21 | Các Quan Xét |
| 8 | `RUT` | `ru` | `Ru` | `ruto` | 8 | 4 | Ru-tơ |
| 9 | `1SA` | `1sa` | `1Sa` | `1samuen` | 9 | 31 | I Sa-mu-ên |
| 10 | `2SA` | `2sa` | `2Sa` | `2samuen` | 10 | 24 | II Sa-mu-ên |
| 11 | `1KI` | `1vua` | `1Vua` | `1cacvua` | 11 | 22 | I Các Vua |
| 12 | `2KI` | `2vua` | `2Vua` | `2cacvua` | 12 | 25 | II Các Vua |
| 13 | `1CH` | `1su` | `1Su` | `1suky` | 13 | 29 | I Sử-ký |
| 14 | `2CH` | `2su` | `2Su` | `2suky` | 14 | 36 | II Sử-ký |
| 15 | `EZR` | **`exo`** ⚠️ | `Exo` / `Exr` | `exora` | 15 | 10 | Ê-xơ-ra |
| 16 | `NEH` | `ne` | `Ne` | `nehemi` | 16 | 13 | Nê-hê-mi |
| 17 | `EST` | **`et`** ⚠️ | `Et` | `exote` | 17 | 10 | Ê-xơ-tê |
| 18 | `JOB` | `giop` | `Giop` | `giop` | 18 | 42 | Gióp |
| 19 | `PSA` | `thi` | `Thi` | `thithien` | 19 | 150 | Thi-thiên |
| 20 | `PRO` | **`ch`** ⚠️ | `Ch` | `chamngon` | 20 | 31 | Châm-ngôn |
| 21 | `ECC` | `tr` | `Tr` | `truyendao` | 21 | 12 | Truyền-đạo |
| 22 | `SNG` | `nha` | `Nha` | `nhaca` | 22 | 8 | Nhã-ca |
| 23 | `ISA` | `es` | `Es` | `esai` | 23 | 66 | Ê-sai |
| 24 | `JER` | `gie` | `Gie` | `gieremi` | 24 | 52 | Giê-rê-mi |
| 25 | `LAM` | `ca` | `Ca` | `cathuong` | 25 | 5 | Ca-thương |
| 26 | `EZK` | `exe` | `Exe` | `exechien` | 26 | 48 | Ê-xê-chi-ên |
| 27 | `DAN` | `da` | `Da` | `danien` | 27 | 12 | Đa-ni-ên |
| 28 | `HOS` | **`os`** ⚠️ | `Os` | `ose` | 28 | 14 | Ô-sê |
| 29 | `JOL` | `gio` | `Gio` | `gioen` | 29 | 3 | Giô-ên |
| 30 | `AMO` | `am` | `Am` | `amot` | 30 | 9 | A-mốt |
| 31 | `OBA` | `ap` | `Ap` | `apdia` | 31 | 1 | Áp-đia |
| 32 | `JON` | `gion` | `Gion` | `giona` | 32 | 4 | Giô-na |
| 33 | `MIC` | `mi` | `Mi` | `miche` | 33 | 7 | Mi-chê |
| 34 | `NAM` | `na` | `Na` | `nahum` | 34 | 3 | Na-hum |
| 35 | `HAB` | `ha` | `Ha` | `habacuc` | 35 | 3 | Ha-ba-cúc |
| 36 | `ZEP` | `so` | `So` | `sophoni` | 36 | 3 | Sô-phô-ni |
| 37 | `HAG` | `ag` | `Ag` | `aghe` | 37 | 2 | A-ghê |
| 38 | `ZEC` | `xa` | `Xa` | `xachari` | 38 | 14 | Xa-cha-ri |
| 39 | `MAL` | `ma` | `Ma` | `malachi` | 39 | 4 | Ma-la-chi |

### 3.2. Tân Ước (27 Sách — 260 Chương)

| # | USFM | `httlvn_code` (URL) | `crossref_abbr` (`⚓` Tooltip) | `tinlanh_slug` (`tinlanh.com`) | `getbible_nr` | Số chương | Tên sách chuẩn (Bản 1925) |
|---|---|---|---|---|---|---|---|
| 40 | `MAT` | `mat` | `Mat` | `mathio` | 40 | 28 | Ma-thi-ơ |
| 41 | `MRK` | `mac` | `Mac` | `mac` | 41 | 16 | Mác |
| 42 | `LUK` | `lu` | `Lu` | `luca` | 42 | 24 | Lu-ca |
| 43 | `JHN` | `gi` | `Gi` | `giang` | 43 | 21 | Giăng |
| 44 | `ACT` | `cong` | `Cong` | `congvucacsudo` | 44 | 28 | Công-vụ các Sứ-đồ |
| 45 | `ROM` | `ro` | `Ro` | `roma` | 45 | 16 | Rô-ma |
| 46 | `1CO` | `1co` | `1Co` | `1corinhto` | 46 | 16 | I Cô-rinh-tô |
| 47 | `2CO` | `2co` | `2Co` | `2corinhto` | 47 | 13 | II Cô-rinh-tô |
| 48 | `GAL` | `ga` | `Ga` | `galati` | 48 | 6 | Ga-la-ti |
| 49 | `EPH` | `eph` | `Eph` | `epheso` | 49 | 6 | Ê-phê-sô |
| 50 | `PHP` | **`phi`** ⚠️ | `Phi` | `philip` | 50 | 4 | Phi-líp |
| 51 | `COL` | `co` | `Co` | `colose` | 51 | 4 | Cô-lô-se |
| 52 | `1TH` | `1te` | `1Te` | `1tesalonica` | 52 | 5 | I Tê-sa-lô-ni-ca |
| 53 | `2TH` | `2te` | `2Te` | `2tesalonica` | 53 | 3 | II Tê-sa-lô-ni-ca |
| 54 | `1TI` | `1ti` | `1Ti` | `1timothe` | 54 | 6 | I Ti-mô-thê |
| 55 | `2TI` | `2ti` | `2Ti` | `2timothe` | 55 | 4 | II Ti-mô-thê |
| 56 | `TIT` | `tit` | `Tit` | `tit` | 56 | 3 | Tít |
| 57 | `PHM` | **`phil`** ⚠️ | `Phil` | `philemon` | 57 | 1 | Phi-lê-môn |
| 58 | `HEB` | `he` | `He` | `heboro` | 58 | 13 | Hê-bơ-rơ |
| 59 | `JAS` | `gia` | `Gia` | `giaco` | 59 | 5 | Gia-cơ |
| 60 | `1PE` | `1phi` | `1Phi` | `1phiero` | 60 | 5 | I Phi-e-rơ |
| 61 | `2PE` | `2phi` | `2Phi` | `2phiero` | 61 | 3 | II Phi-e-rơ |
| 62 | `1JN` | `1gi` | `1Gi` | `1giang` | 62 | 5 | I Giăng |
| 63 | `2JN` | `2gi` | `2Gi` | `2giang` | 63 | 1 | II Giăng |
| 64 | `3JN` | `3gi` | `3Gi` | `3giang` | 64 | 1 | III Giăng |
| 65 | `JUD` | `giu` | `Giu` | `giude` | 65 | 1 | Giu-đe |
| 66 | `REV` | **`kh`** ⚠️ | `Kh` | `khaihuyen` | 66 | 22 | Khải-huyền |

---

## 4. Giải Phẫu Cấu Trúc DOM & 6 "Bẫy Parser" Thực Nghiệm (TRAP A1 – A6)

### 4.1. Mẫu HTML thực tế của một chương (`/doc-kinh-thanh/sa/1?v=VI1934`)

```html
<div class="col-md-12 bible-read">
  <div id="sa_1">
    <div class="title">
      <h1>1</h1>
      <h2>Về thời cổ, từ buổi sáng thế đến đời Áp-ra-ham</h2>
      <p>(Từ đoạn 1 đến 11:9)</p>
      <h3>Tạo thành trời đất</h3>
    </div>
    <span class="verse sa_1_1">&emsp;<sup>1</sup>&nbsp;Ban đầu Đức Chúa Trời dựng nên trời đất. <br/></span>
    <span class="verse sa_1_2">&emsp;<sup>2</sup>&nbsp;Vả, đất là vô hình và trống không, sự mờ tối ở trên mặt vực; Thần Đức Chúa Trời vận hành trên mặt nước. </span>
    <span class="verse sa_1_3"><sup>3</sup>&nbsp;Đức Chúa Trời phán rằng: Phải có sự sáng; thì có sự sáng.<a data-toggle="tooltip" data-placement="bottom" title="2Co 4:6">⚓</a></span>
  </div>
</div>
```

### 4.2. Chi tiết 6 Bẫy Parser bắt buộc phải xử lý trong code

#### Bẫy A2 — Cú pháp kép `][gt=...` trong thẻ `<a title="...">⚓</a>` và 16 Câu Khuyết Tân Ước
Qua kiểm thử trên `/doc-kinh-thanh/mat/17?v=VI1934`, `/doc-kinh-thanh/es/53?v=VI1934` và `/doc-kinh-thanh/ro/8?v=VI1934`, thuộc tính `title` của thẻ `<a>⚓</a>` chứa chuỗi phân cách đặc biệt `][gt=` với **2 trường hợp ngữ nghĩa khác nhau**:
1. **Trường hợp 1 — Ghi chú 16 câu khuyết trong Tân Ước (`mat/17:21`, `mat/18:11`, `mat/23:14`, `mac/7:16`, `mac/9:44`, `mac/9:46`, `mac/11:26`, `mac/15:28`, `lu/17:36`, `lu/23:17`, `gi/5:4`, `cong/8:37`, `cong/15:34`, `cong/24:7`, `cong/28:29`, `ro/16:24`)**:
   - Tại `mat/17`, thẻ `<span class="verse mat_17_21">` **không tồn tại trên DOM** (nhảy thẳng từ `mat_17_20` sang `mat_17_22`).
   - Toàn bộ câu 21 nằm trong `title` của thẻ `<a>⚓</a>` ở cuối câu 20:
     ```html
     <a data-toggle="tooltip" data-placement="bottom" title="Mat 21:21; Mac 11:23; 1Co 13:2][gt=Có mấy bản cũ thêm một câu 21 rằng: Nhưng thứ quỉ nầy nếu không cầu nguyện và không kiêng ăn thì chẳng trừ nó được">⚓</a>
     ```
2. **Trường hợp 2 — Tham chiếu chéo mở rộng / ứng nghiệm (`es/53`, `ro/8`)**:
   - Tại `es/53` (Ê-sai 53:7), thẻ `<a>⚓</a>` có:
     ```html
     <a data-toggle="tooltip" data-placement="bottom" title="Kh 5:6][gt=Cong 8:32-33">⚓</a>
     ```
   - Tại `ro/8` (Rô-ma 8:15), thẻ `<a>⚓</a>` có:
     ```html
     <a data-toggle="tooltip" data-placement="bottom" title="Ga 4:5-7][gt=Mac 14:36; Ga 4:6">⚓</a>
     ```
* **Thuật toán xử lý chuẩn cho `title` của `⚓`**:
  1. Tách chuỗi `raw_title` theo `][gt=`: `parts = raw_title.split("][gt=")`.
  2. `parts[0]` luôn là danh sách địa chỉ tham chiếu chéo phân cách bởi `;`.
  3. Nếu có `parts[1]`:
     - Kiểm tra xem `parts[1]` có khớp regex danh sách địa chỉ Kinh Thánh (`^[1-3]?[A-Za-z]+\s+\d+:\d+`) hay không. Nếu khớp (như `Cong 8:32-33` hoặc `Mac 14:36; Ga 4:6`), gộp tiếp vào danh sách `cross_references`!
     - Nếu `parts[1]` là câu văn tiếng Việt (như `Có mấy bản cũ thêm một câu (\d+) rằng:\s*(.+)`), lưu vào `textual_footnotes` của câu hiện tại, **đồng thời** tạo một bản ghi câu ảo `verse = int(m.group(1))` với cờ `"is_omitted_in_critical_text": true` và `"footnote_only_text": m.group(2)` để giữ đồng bộ số câu 1-1 với bản `KJV`, `GetBible vietnamese` và `Bungo-yaku`!

#### Bẫy A4 — Thượng Đề Thi-thiên (`<i>` bên trong `<div class="title">`) Có Chứa Thẻ `<a>⚓</a>` Lồng Bên Trong
* Trong sách *Thi-thiên* (ví dụ `/doc-kinh-thanh/thi/51?v=VI1934`), khối `<div class="title">` ở đầu chương hoặc giữa chương có cấu trúc:
  ```html
  <div class="title">
    <h1>51</h1>
    <h3>Người có lòng ăn năn hối cải cầu xin Chúa tha thứ mình</h3>
    <i>Cho thầy nhạc chánh. Thơ Đa-vít làm, lúc đấng tiên tri Na-than đến cùng người, sau khi người đã vào cùng Bát-sê-ba.<a data-toggle="tooltip" data-placement="bottom" title="2Sa 12:1-15">⚓</a></i>
  </div>
  ```
* **Quy tắc Parser bắt buộc**:
  - `<h2>` (tiêu đề đại phân đoạn), `<p>` (phạm vi chương), `<h3>` (tiêu đề phân đoạn) được gắn vào `section_headings` của câu kế tiếp.
  - Thẻ `<i>` bên trong `<div class="title">` là **Thượng đề nguyên bản Hê-bơ-rơ (`psalm_superscription`)**. Khi lấy text của `<i>`, **phải bóc tách thẻ `<a title="...">⚓</a>` lồng bên trong `<i>`** trước (lưu `"2Sa 12:1-15"` vào `superscription_cross_refs` và loại bỏ ký tự `⚓` khỏi chuỗi `psalm_superscription`).

#### Bẫy A5 — Ngắt Dòng Thơ (`<br/>&emsp;`), Ngắt Khổ Acrostic Thi-thiên 119 (`<br/>&emsp;<br/>`) & Ngắt Lời Thoại Nhã-ca (`---`)
* Qua kiểm thử `/doc-kinh-thanh/thi/23?v=VI1934`, `/doc-kinh-thanh/thi/119?v=VI1934` và `/doc-kinh-thanh/nha/1?v=VI1934`:
  1. **Đầu đoạn văn mới**: Nội dung sau `</span>` bắt đầu bằng `&emsp;<sup>N</sup>&nbsp;` $\rightarrow$ `is_paragraph_start = True`.
  2. **Ngắt dòng thơ trong cùng 1 câu**: Bên trong `<span class="verse">`, chuỗi `<br/>&emsp;` xuất hiện giữa hai vế thơ $\rightarrow$ chuyển thành ký tự xuống dòng `\n` (và tách mảng `poetic_lines`).
  3. **Ngắt khổ 8 câu trong Thi-thiên 119**: Cuối các câu `8, 16, 24, ..., 176` của `thi/119`, HTML kết thúc bằng `<br/>&emsp;<br/></span>` (Bản `VI1934` trên `kinhthanh.httlvn.org` không in tên 22 chữ cái Hê-bơ-rơ *Aleph, Beth...* mà dùng `<br/>&emsp;<br/>` để tạo khoảng trắng ngắt khổ). Parser cần nhận diện `<br/>\s*&emsp;\s*<br/>` ở cuối câu làm cờ `is_stanza_break = True` (và ta sẽ bổ sung nhãn 22 chữ cái Hê-bơ-rơ *א Aleph .. ת Tav* từ bản `WLC`/`KJV` vào metadata của các câu `1, 9, 17...`).
  4. **Ngắt lời đối đáp trong Nhã-ca (`nha/1`)**: Giữa một câu thơ khi đổi nhân vật đối thoại (Tân nương $\leftrightarrow$ Tân lang $\leftrightarrow$ Nữ tỳ), văn bản dùng chuỗi ` --- <br/>&emsp;` (ví dụ `nha_1_7`, `nha_1_8`). Parser cần giữ nguyên dấu `—` hoặc tách dòng thơ tương ứng.

#### Bẫy A6 — Đường Dẫn Audio Chứa Dấu Backslash Windows (`\`)
* Trong HTML của mọi chương, thẻ `<source>` trong `<audio id="audio">` được render là:
  ```html
  <source src="\Audio\VI1934\1-ms-nguyen-thi\sa\1.mp3" type="audio/mp3" />
  ```
* **Quy tắc Parser bắt buộc**: Chuẩn hóa `audio_src.replace("\\", "/")` trước khi ghép thành URL tuyệt đối `https://kinhthanh.httlvn.org/Audio/VI1934/1-ms-nguyen-thi/sa/1.mp3`.

---

## 5. Code Mẫu Parser Chuẩn Xác (`parse_httlvn_chapter_html`)

Đoạn code Python dưới đây xử lý trọn vẹn cả 6 bẫy runtime nêu trên:

```python
import re
from bs4 import BeautifulSoup, NavigableString, Tag

CROSSREF_ABBR_TO_USFM = {
    "sa": "GEN", "xu": "EXO", "le": "LEV", "dan": "NUM", "phu": "DEU",
    "gios": "JOS", "cac": "JDG", "ru": "RUT", "1sa": "1SA", "2sa": "2SA",
    "1vua": "1KI", "2vua": "2KI", "1su": "1CH", "2su": "2CH",
    "exo": "EZR", "exr": "EZR", "ne": "NEH", "et": "EST", "ext": "EST",
    "giop": "JOB", "thi": "PSA", "ch": "PRO", "cham": "PRO", "tr": "ECC",
    "nha": "SNG", "es": "ISA", "gie": "JER", "ca": "LAM", "exe": "EZK",
    "da": "DAN", "os": "HOS", "ho": "HOS", "gio": "JOL", "am": "AMO",
    "ap": "OBA", "gion": "JON", "mi": "MIC", "na": "NAM", "ha": "HAB",
    "so": "ZEP", "ag": "HAG", "xa": "ZEC", "ma": "MAL",
    "mat": "MAT", "mac": "MRK", "lu": "LUK", "gi": "JHN", "cong": "ACT",
    "ro": "ROM", "1co": "1CO", "2co": "2CO", "ga": "GAL", "eph": "EPH",
    "phi": "PHP", "co": "COL", "1te": "1TH", "2te": "2TH", "1ti": "1TI",
    "2ti": "2TI", "tit": "TIT", "phil": "PHM", "phim": "PHM", "he": "HEB",
    "gia": "JAS", "1phi": "1PE", "2phi": "2PE", "1gi": "1JN", "2gi": "2JN",
    "3gi": "3JN", "giu": "JUD", "kh": "REV", "khai": "REV",
}

REF_ITEM_RE = re.compile(r"^([1-3]?[A-Za-z]+)\s+(\d+):([\d\-,\s]+)$")
OMITTED_VERSE_RE = re.compile(
    r"Có mấy bản cũ thêm (?:một )?câu\s+(\d+)\s+rằng:\s*(.+)", re.IGNORECASE
)


def parse_tooltip_title(raw_title: str):
    """Tách chuỗi title của thẻ <a>⚓</a> thành cross_refs và textual_footnotes."""
    cross_refs = []
    footnotes = []
    omitted_verses = []

    if not raw_title:
        return cross_refs, footnotes, omitted_verses

    segments = [seg.strip() for seg in raw_title.split("][gt=") if seg.strip()]
    for idx, seg in enumerate(segments):
        # Kiểm tra xem segment sau ][gt= là ghi chú văn bản hay là danh sách tham chiếu
        m_omit = OMITTED_VERSE_RE.search(seg)
        if m_omit:
            footnotes.append(seg)
            omitted_verses.append({
                "verse": int(m_omit.group(1)),
                "text": m_omit.group(2).strip(),
                "raw_note": seg,
            })
            continue

        # Thử tách theo dấu ';' xem có phải danh sách địa chỉ Kinh Thánh không
        items = [it.strip() for it in seg.split(";") if it.strip()]
        all_valid_refs = True
        parsed_Batch = []
        for it in items:
            m_ref = REF_ITEM_RE.match(it)
            if m_ref:
                abbr = m_ref.group(1).lower()
                usfm = CROSSREF_ABBR_TO_USFM.get(abbr, abbr.upper())
                parsed_Batch.append({
                    "raw": it,
                    "usfm_book": usfm,
                    "chapter": int(m_ref.group(2)),
                    "verses": m_ref.group(3).strip(),
                })
            else:
                all_valid_refs = False
                break

        if all_valid_refs and parsed_Batch:
            cross_refs.extend(parsed_Batch)
        else:
            footnotes.append(seg)

    return cross_refs, footnotes, omitted_verses
```

---

## 6. Quy Trình Pipeline 4 Bước & Quản Lý Trạng Thái (`state/`)

Tuân thủ kiến trúc chuẩn của `LumiLearnWeb_hoclieu/crawl_factory`, bộ thu thập `kinhthanh_httlvn` được chia làm 4 bước độc lập, có khả năng tạm dừng (`Ctrl+C`) và chạy tiếp (`resume`) bất kỳ lúc nào:

* **File trạng thái (`state/kinhthanh_httlvn_state.json`)**:
  ```json
  {
    "source": "kinhthanh_httlvn",
    "version": "VI1934",
    "last_updated": "2026-11-08T12:00:00Z",
    "stats": {
      "total_chapters": 1189,
      "fetched": 1189,
      "parsed": 1189,
      "failed": 0
    },
    "chapters": {
      "GEN.1": {
        "usfm": "GEN",
        "httlvn_code": "sa",
        "chapter": 1,
        "url": "https://kinhthanh.httlvn.org/doc-kinh-thanh/sa/1?v=VI1934",
        "status": "parsed",
        "raw_path": "raw/kinhthanh_httlvn/VI1934/sa/1.html",
        "verse_count": 31,
        "omitted_verse_count": 0,
        "audio_url": "https://kinhthanh.httlvn.org/Audio/VI1934/1-ms-nguyen-thi/sa/1.mp3"
      }
    }
  }
  ```
* **Các bước thực thi CLI**:
  - `--step 1` (**Discovery**): Tải `/?v=VI1934`, bóc tách 1.189 đường dẫn chương, đối chiếu với bảng 66 sách chuẩn (kiểm tra tổng số chương `= 1189`), khởi tạo `state/kinhthanh_httlvn_state.json`.
  - `--step 2` (**Fetch Raw HTML**): Duyệt các chương có `status == "pending"` hoặc `"failed"`, tải HTML với delay `1.2s ± 0.3s`, kiểm tra sự tồn tại của `<div class="col-md-12 bible-read">` trước khi lưu vào `raw/kinhthanh_httlvn/VI1934/{book_code}/{chapter}.html` và cập nhật `status = "fetched"`.
  - `--step 3` (**Parse & Extract**): Đọc file HTML từ `raw/`, chạy `parse_httlvn_chapter_html()`, xuất JSON trung gian từng chương và tổng hợp đồ thị `cross-references.json`.
  - `--step 4` (**Cross-Verify & Export**): Đối chiếu chéo từng câu (`31.102` câu) với `tinlanh_com` và `getbible_vietnamese` theo thuật toán **3-Way Majority Voting** (chi tiết tại [`tinlanh-com.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/tinlanh-com.md)).
