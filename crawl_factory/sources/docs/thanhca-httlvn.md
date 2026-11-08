# `thanhca.httlvn.org` — Thánh Ca Tin Lành (903 Bài) & Kinh Thánh Đối Đáp (100 Bài)

* **Source ID**: `thanhca_httlvn`
* **Trang gốc**: `https://thanhca.httlvn.org`
* **Ngày khảo sát & Reverse Engineering**: 08/11/2026
* **Vai trò trong hệ sinh thái `fukuin_hoclieu`**: Nguồn chuẩn số 1 (Primary Source) cho trọn bộ **903 bài Thánh Ca Tin Lành** (lời, hợp âm ChordPro, thông tin nhạc sĩ / dịch giả, phân loại chủ đề 2 cấp, bản nhạc `MusicXML`, danh sách MP3 / Beat / Karaoke, cấu trúc slide PowerPoint) và **100 bài Kinh Thánh Đối Đáp (KTĐĐ)**.

---

## 1. Kiến Trúc Server, Endpoints & Chiến Lược Tối Ưu Hóa Lưu Lượng (Giảm 78% Request)

### 1.1. Hạ tầng Server & Chống Crawl
* **Web Server**: `Microsoft-IIS/10.0` (ASP.NET MVC 5), không có Cloudflare challenge (`CF-RAY: None`), không có CAPTCHA.
* **Bẫy Kiến Trúc Cực Lớn Khi Crawl 7 Tab (`Lời`, `Hợp âm`, `Sheet`, `Nhạc`, `Beat`, `Karaoke`, `PPT`)**:
  Qua kiểm thử thực nghiệm trên các bài số `1`, `7`, `9`, `42`, `500`, `903`:
  1. Thanh điều hướng `<ul class="nav nav-tabs nav-details" role="tablist">` trên đầu mỗi trang bài hát **luôn luôn hiển thị cứng cả 7 tab** cho mọi bài từ `1..903`, **ngay cả khi bài đó KHÔNG hề có Hợp âm, KHÔNG có MP3, KHÔNG có Beat hay Karaoke**!
     - Ví dụ thực nghiệm tại Bài 9 (`/thanh-ca-9/uoc-thuat-chuyen-tuyet-doi`):
       - `?op=chords` trả về `has_chords = False` (chỉ có lời thường, không có thẻ hợp âm).
       - `?op=mp3` trả về `mp3 = []` (không có thẻ `<audio>`).
       - `?op=beat` trả về `yt = []` (không có `<iframe>` YouTube).
       - `?op=karaoke` trả về `yt = []` (không có `<iframe>` YouTube).
  2. Nếu crawler ngây thơ quét $903 \times 7 = \mathbf{6.321\text{ requests}}$, hơn 65% số request sẽ trả về tab rỗng vô ích!

### 1.2. Phát hiện "Mỏ Vàng" Từ Các Trang Mục Lục Lọc (`?op=...`) & Playlist MP3
Kiểm thử thực nghiệm các trang mục lục `/thanh-ca?op={op}` và DOM của từng tab cho thấy:
1. **Hợp nhất Tab `Lời` và Tab `Hợp âm` (`?op=chords`) chỉ trong 1 Request / bài**:
   - Trang `/thanh-ca-{id}/{slug}?op=chords` chứa **đầy đủ 100% nội dung của tab `Lời`** (tiêu đề, nhạc sĩ, người dịch, toàn bộ các câu hát) **cộng thêm** các thẻ `<i class="chord-group"><span class="hopam">[G]</span>...</i>` (nếu bài đó có hợp âm).
   - Khi bóc tách `?op=chords`: giữ thẻ `<span class="hopam">` sẽ thu được bản **ChordPro**, và loại bỏ `<span class="hopam">.*?</span>` sẽ thu được bản **Lời thuần túy (Clean Lyrics)** chính xác tuyệt đối! $\rightarrow$ **Tiết kiệm ngay 903 requests của tab `Lời`!**
2. **Lấy trọn bộ danh sách 384 bài có Nhạc MP3 chỉ bằng 1 Request duy nhất**:
   - Trên trang `/thanh-ca-1/cui-xin-vua-thanh-ngu-lai?op=mp3`, khối `<div class="list-group audio-player-playlist">` liệt kê sẵn **đầy đủ 384 bài Thánh Ca có file MP3** (`#001, #002, #003, #004, #005, #006, #008, #010, #011, #015...`).
   - URL file MP3 hoàn toàn tất định: `https://audio.httlvn.org/TC/thanh-ca/mp3/{id}.mp3`. $\rightarrow$ **Tiết kiệm 902 requests của tab `Nhạc`!**
3. **Mục lục lọc trước cho `Beat` và `Karaoke` (chỉ 5 trang mỗi loại)**:
   - `/thanh-ca?op=beat&page={1..5}` chỉ gồm **5 trang** ($\le 250$ bài có video Beat YouTube).
   - `/thanh-ca?op=karaoke&page={1..5}` chỉ gồm **5 trang** ($\le 250$ bài có video Karaoke YouTube).
   - Crawler chỉ cần quét 5 trang mục lục này để lập danh sách ID có Beat/Karaoke rồi mới tải chi tiết `?op=beat` / `?op=karaoke` cho đúng các bài đó! $\rightarrow$ **Tiết kiệm ~1.350 requests rỗng!**
4. **Endpoint trực tiếp cho `MusicXML Sheet` và `PowerPoint`**:
   - Sheet nhạc `MusicXML`: gọi thẳng `/Download/SheetMusic/{id}` (hoặc `/Data/thanh-ca/sheet/{id}.xml`).
   - Slide trình chiếu HTML: `/Home/Powerpoint/{id}` (chứa sẵn cấu trúc `<div id="carousel-ppt">` chia từng câu/điệp khúc thành từng slide `<div class="item">`).

### 1.3. Bảng tổng hợp URL Endpoints & Số lượng Request tối ưu

| Phân mục | URL Pattern | Quy mô thực tế | Số Request cần gọi |
|---|---|---|---|
| Mục lục Thánh Ca tổng (19 trang) | `/thanh-ca?page={1..19}` | **903 bài** (`18 × 50 + 3`) | `19` requests |
| Mục lục lọc Beat / Karaoke | `/thanh-ca?op={beat\|karaoke}&page={1..5}` | ~200–250 bài / loại | `10` requests |
| Playlist toàn bộ 384 bài có MP3 | `/thanh-ca-1/cui-xin-vua-thanh-ngu-lai?op=mp3` | **384 bài** có MP3 | `1` request |
| Chi tiết Lời + Hợp âm + Metadata | `/thanh-ca-{id}/{slug}?op=chords` | **903 bài** | `903` requests |
| File bản nhạc số `MusicXML` | `/Download/SheetMusic/{id}` | ~550–650 bài có XML | `903` requests (bắt `404`) |
| Chi tiết YouTube ID (`Beat` / `Karaoke`) | `/thanh-ca-{id}/{slug}?op={beat\|karaoke}` | Chỉ gọi cho bài nằm trong mục lục lọc | `~420` requests |
| Mục lục Kinh Thánh Đối Đáp | `/kinh-thanh-doi-dap` | **100 bài** (`001..100`) | `1` request |
| Chi tiết Kinh Thánh Đối Đáp | `/kinh-thanh-doi-dap-{id}/{slug}` | **100 bài** | `100` requests |

---

## 2. Giải Phẫu Cấu Trúc DOM Của Từng Tab & 6 "Bẫy Parser" (TRAP D3 – D8)

> [!CAUTION]
> **BẪY RUNTIME D3 — Khác Biệt Hoàn Toàn Về Container DOM Giữa 7 Tab**:
> Thẻ `<div id="details-content">` **CHỈ TỒN TẠI** trên 2 tab `Lời` (mặc định) và `Hợp âm` (`?op=chords`)!
> Nếu dùng selector `#details-content` trên các tab `mp3`, `beat`, `karaoke`, `ppt`, `sheet`, parser sẽ nhận về `None`! Bảng dưới đây ghi rõ container DOM chính xác của từng tab đã xác minh thực nghiệm:

| Tab (`?op=...`) | Container DOM chính trong `<div class="tab-content">` | Các phần tử con quan trọng bên trong |
|---|---|---|
| Mặc định (`Lời`) & `?op=chords` | `<div id="details-content">` | `<div class="row mt-2">` (Nhạc sĩ / Dịch giả), `<h1>` (Số bài & Tên bài), `<div id="lyric-content">` (Lời & `<i class="chord-group"><span class="hopam">`) |
| `?op=sheet` | `<div role="tabpanel" class="tab-pane active sheet">` | `<div id="sheet-content" class="osmdContainer"></div>` + script nạp `/Data/thanh-ca/sheet/{id}.xml` |
| `?op=mp3` | `<div role="tabpanel" class="tab-pane active mp3">` | `<div class="audio-player">...<audio id="audio-player"><source src="https://audio.httlvn.org/TC/thanh-ca\mp3/1.mp3"/></audio></div>` + `<div class="list-group audio-player-playlist">` (chứa 384 thẻ `<a>`) |
| `?op=beat` & `?op=karaoke` | `<div role="tabpanel" class="tab-pane active beat">` (hoặc `karaoke`) | `<div class="embed-responsive ..."><iframe src="https://www.youtube.com/embed/{yt_id}?rel=0"></iframe></div>` + `<div id="video-content">` + `<div class="collapse" id="collapseLyric">` |
| `?op=ppt` | `<div role="tabpanel" class="tab-pane active ppt">` | `<div id="ppt-content"><iframe id="ppt-iframe" src="/Home/Powerpoint/{id}"></iframe><form action="/Download/Powerpoint/{id}">...</form></div>` |

### 2.1. Bẫy D4 — Hai Họ Cấu Trúc HTML Khác Nhau Trong `<div id="lyric-content">`
Qua khảo sát đối chiếu giữa Bài 1 (`/thanh-ca-1?op=chords`), Bài 42 (`/thanh-ca-42?op=chords`) và Bài 903 (`/thanh-ca-903?op=chords`), dữ liệu lời bài hát trên `thanhca.httlvn.org` do nhiều đợt nhập liệu khác nhau nên tồn tại **2 họ cấu trúc DOM**:

* **Họ DOM Kiểu A (Các bài đầu như Bài 1 — Gộp cả khổ vào 1 thẻ `<p>`)**:
  ```html
  <div id="lyric-content">
    <p>
      <b>B1L</b>
      <i class="chord-group"><span class="hopam">[G]</span>1.Cúi</i> xin Vua
      <i class="chord-group"><span class="hopam">[C]</span>Thánh</i>
      <i class="chord-group"><span class="hopam">[D7]</span>ngự</i>
      <i class="chord-group"><span class="hopam">[G]</span>lai,</i><br/>
      Hộ tôi cung <i class="chord-group"><span class="hopam">[Am]</span>chúc</i> danh <i class="chord-group"><span class="hopam">[D7]</span>Ngài</i>;
    </p>
  </div>
  ```
  - Lưu ý thẻ `<b>B1L</b>` ở đầu đoạn là mã ký hiệu phân loại/điệu nhạc nội bộ, **không phải** lời hát!
* **Họ DOM Kiểu B (Các bài như Bài 42, Bài 903 — Tách từng dòng thành `<p>` riêng kèm nhãn `<p><b>Câu X</b></p>`)**:
  ```html
  <div id="lyric-content">
    <p><b>Câu 1</b></p>
    <p>1. Gần tường thành xưa Giê-<i class="chord-group"><span class="hopam">[Eb]</span>ru</i>-sa-lem,</p>
    <p>Nơi chuồng chiên tối tăm hèn,</p>
    <p></p>
    <p><b>Điệp khúc</b></p>
    <p>Ha-lê-lu-gia! Ha-lê-lu-gia!</p>
  </div>
  ```
* **Thuật toán chuẩn hóa Stanza (`parse_hymn_lyrics_and_chords`)**:
  1. Bỏ qua các thẻ `<p></p>` rỗng và bóc riêng thẻ `<b>B1L</b>` (regex `^[A-Z]\d+[A-Z]?$`) vào trường `meter_code`.
  2. Nếu trong `#lyric-content` có các thẻ `<p><b>(Câu \d+|Điệp khúc|ĐK:?)</b></p>`, dùng chính các thẻ này làm ranh giới ngắt `stanzas` (`type: "verse"` hoặc `"chorus"`).
  3. Nếu không có `<p><b>Câu X</b></p>`, duyệt từng thẻ `<p>`: tách dòng theo `<br/>`, kiểm tra tiền tố `^(\d+)\.` hoặc `^(Điệp khúc|ĐK):?` để phân loại stanza.

### 2.2. Bẫy D5 — Thẻ `<i class="chord-group">` Chèn Giữa Từ Ghép Có Gạch Nối (`Giê-[Eb]ru-sa-lem`)
* Tại Bài 903 (`?op=chords`), hợp âm được đặt ngay ở âm tiết thứ hai của danh từ riêng có gạch nối:
  ```html
  Gần tường thành xưa Giê-<i class="chord-group"><span class="hopam">[Eb]</span>ru</i>-sa-lem
  ```
* **Cảnh báo lỗi kinh điển**: Nếu dùng `BeautifulSoup.get_text(separator=" ")` hoặc chèn khoảng trắng khi unwrap thẻ `<i>`, từ `Giê-ru-sa-lem` sẽ bị biến dạng thành `Giê- [Eb] ru -sa-lem` (hoặc ở bản lời sạch biến thành `Giê- ru -sa-lem`)!
* **Quy tắc xử lý bắt buộc**:
  - **Để sinh dòng ChordPro (`chordpro_line`)**: Duyệt từng thẻ `<i class="chord-group">`, lấy chuỗi hợp âm trong `<span class="hopam">` (ví dụ `[Eb]`) ghép liền kề với phần text âm tiết còn lại trong `<i>` (`ru`) thành `[Eb]ru`, rồi `.replace_with("[Eb]ru")` trực tiếp trên cây DOM **không thêm bất kỳ khoảng trắng nào** $\rightarrow$ kết quả chuẩn: `Giê-[Eb]ru-sa-lem`.
  - **Để sinh dòng Lời sạch (`clean_line`)**: Trước tiên `.decompose()` toàn bộ các thẻ `<span class="hopam">`, sau đó `.unwrap()` các thẻ `<i class="chord-group">` rồi mới đọc text $\rightarrow$ kết quả chuẩn: `Giê-ru-sa-lem`.

### 2.3. Bẫy D6 — Dấu Backslash Windows (`\`) Trong URL Audio MP3
* Tương tự `kinhthanh.httlvn.org`, thẻ `<source>` trong tab `?op=mp3` của `thanhca.httlvn.org` chứa dấu backslash ngược:
  `https://audio.httlvn.org/TC/thanh-ca\mp3/1.mp3`
* **Quy tắc bắt buộc**: Luôn gọi `.replace("\\", "/")` thành `https://audio.httlvn.org/TC/thanh-ca/mp3/1.mp3`.

### 2.4. Bẫy D7 — Xử Lý `HTTP 404` Êm Ái Khi Tải `MusicXML` (`/Download/SheetMusic/{id}`)
* Khi gửi `GET https://thanhca.httlvn.org/Download/SheetMusic/{id}`:
  - Các bài có bản nhạc số (`id = 1, 42, 500...`) trả về `HTTP 200 OK`, header `Content-Type: application/vnd.recordare.musicxml+xml`, nội dung XML bắt đầu bằng `<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE score-partwise...`.
  - Các bài chưa được số hóa MusicXML (`id = 903...`) trả về `HTTP 404 Not Found`.
* **Quy tắc Crawler**: Trong `CrawlerCore`, mã `HTTP 404` đối với endpoint `/Download/SheetMusic/{id}` **không phải là lỗi mạng cần retry**, mà phải ghi nhận ngay `musicxml_status = "not_available"` trong file state và chuyển sang bài tiếp theo.

---

## 3. Phân Tích Kỹ Thuật Mục Kinh Thánh Đối Đáp (`1..100`) & Bẫy Nhân Đôi Link (TRAP D8)

### 3.1. Bẫy D8 — Nhân Đôi Thẻ `<a>` Trên Trang Mục Lục `/kinh-thanh-doi-dap` (200 Links cho 100 Bài)
* Khi kiểm thử thực nghiệm `GET https://thanhca.httlvn.org/kinh-thanh-doi-dap`, biểu thức `re.findall(r'href="(/kinh-thanh-doi-dap-\d+/[^"]+)"', html)` trả về **200 kết quả**!
* **Nguyên nhân**: Mỗi ô thẻ bài đọc trên giao diện chứa **2 thẻ `<a href="/kinh-thanh-doi-dap-{id}/{slug}">` giống hệt nhau** (1 thẻ bọc tiêu đề số bài và 1 thẻ bọc địa chỉ Kinh Thánh phụ đề).
* **Quy tắc Discovery bắt buộc**: Khử trùng lặp theo `reading_id` (`1..100`) bằng `dict` giữ nguyên thứ tự xuất hiện, đảm bảo đúng **100 bài Kinh Thánh Đối Đáp**.

### 3.2. Cấu trúc DOM Chi Tiết Của Một Bài Kinh Thánh Đối Đáp (`/kinh-thanh-doi-dap-1/dang-tao-hoa`)

```html
<div id="lyric-content" class="mb-1">
  <p>Ban đầu Đức Chúa Trời dựng nên trời đất.</p>
  <blockquote><strong>Vả, đất là vô hình và trống không, sự mờ tối ở trên mặt vực; Thần Đức Chúa Trời vận hành trên mặt nước.</strong></blockquote>
  <p>Đức Chúa Trời phán rằng: Phải có sự sáng; thì có sự sáng.</p>
  <blockquote><strong>Đức Chúa Trời thấy sáng là tốt lành, bèn phân sáng ra cùng tối.</strong></blockquote>
  <p align="right"><em><a href="#" data-bible="sa 1:1-6">Sáng-thế ký 1:1-6</a></em></p>
</div>
```

* **Quy tắc bóc tách (`parse_responsive_reading`)**:
  - Duyệt tuần tự các thẻ con trực tiếp trong `<div id="lyric-content">`:
    1. Nếu là `<p>` có `align="right"` hoặc chứa `<a data-bible="...">`: đây là **chỉ dẫn phân đoạn Kinh Thánh** (`scripture_ref_raw = a["data-bible"]`, ví dụ `"sa 1:1-6"`, dùng bảng `CROSSREF_ABBR_TO_USFM` tại [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) để chuẩn hóa thành `"GEN.1.1-6"`).
    2. Nếu là `<p>` thông thường (không có `data-bible`): lượt đọc của **`leader`** (*Người hướng dẫn / Chủ lễ*).
    3. Nếu là `<blockquote>`: lượt đáp của **`congregation`** (*Hội chúng* — bên trong bọc `<strong>`). Nếu ở cuối bài có câu đồng thanh kết thúc, gắn `role = "all"` hoặc `"congregation"`.

---

## 4. Quy Trình Pipeline 5 Bước & Quản Lý Trạng Thái (`state/thanhca_httlvn_state.json`)

* `--step 1` (**Index & Media Capability Discovery**):
  - Quét `/thanh-ca?page=1..19` lấy danh sách 903 bài (`id`, `slug`, `title`, `cat_top`, `cat_sub`).
  - Quét `/thanh-ca-1/cui-xin-vua-thanh-ngu-lai?op=mp3` lấy tập hợp `mp3_ids` (384 bài).
  - Quét `/thanh-ca?op=beat&page=1..5` lấy tập hợp `beat_ids`.
  - Quét `/thanh-ca?op=karaoke&page=1..5` lấy tập hợp `karaoke_ids`.
  - Quét `/kinh-thanh-doi-dap` (khử trùng 200 $\to$ 100 link) lấy danh sách 100 bài KTĐĐ.
  - Ghi toàn bộ vào `state/thanhca_httlvn_state.json`.
* `--step 2` (**Fetch Lyrics + Chords (`?op=chords`) & Responsive Readings**):
  - Tải 903 trang `/thanh-ca-{id}/{slug}?op=chords` vào `raw/thanhca_httlvn/chords/{id}.html`.
  - Tải 100 trang `/kinh-thanh-doi-dap-{id}/{slug}` vào `raw/thanhca_httlvn/ktdd/{id}.html`.
* `--step 3` (**Fetch Filtered Media Tabs (`beat`, `karaoke`) & `MusicXML`**):
  - Chỉ tải `?op=beat` cho các bài thuộc `beat_ids` và `?op=karaoke` cho các bài thuộc `karaoke_ids`.
  - Tải `/Download/SheetMusic/{id}` vào `raw/thanhca_httlvn/musicxml/{id}.xml` (ghi nhận `404` vào state để không tải lại khi resume).
* `--step 4` (**Parse, Cross-Verify Lyrics with `vietchristian.com/thanhca/thanhca.txt` & Export**):
  - Xuất `hymns/vi-thanh-ca/{1..903}.json` và `responsive-readings/vi-ktdd.json`.
