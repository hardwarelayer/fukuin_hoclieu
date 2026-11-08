# Thiết Kế Kỹ Thuật Lõi Crawler, Quản Lý Trạng Thái, Chống Chặn & Ma Trận 18 Bẫy Runtime (`fukuin_hoclieu/crawl_factory`)

Tài liệu này kế thừa trực tiếp chuẩn kỹ thuật của `LumiLearnWeb_hoclieu/crawl_factory` (`vn_en/docs/technical_design.md`, `vn_jp2/docs/overview.md`) và tổng hợp toàn bộ cơ chế vận hành, quản lý trạng thái (`state/`), cấu hình (`config.json`), cùng **Bảng Kiểm Tra 18 Bẫy Runtime (Runtime Trap Checklist)** đã phát hiện qua kiểm thử thực nghiệm trên các nguồn dữ liệu của `fukuin_hoclieu`.

---

## 1. Chỉ Thị Vận Hành Bắt Buộc Cho AI Agent (Operational Directive)

> [!IMPORTANT]
> **QUY TẮC VẬN HÀNH KHI VIẾT VÀ CHẠY CRAWLER (`AI OPERATIONAL DIRECTIVE`)**:
> 1. **Tuyệt đối không tự ý chạy lệnh Crawl hàng loạt (Full Bulk Crawl)** trong phiên hội thoại của AI Agent (ví dụ tải toàn bộ 1.189 chương Kinh Thánh hay 903 bài Thánh Ca).
> 2. Khi kiểm thử code crawler hoặc parser vừa viết xong, AI Agent **chỉ được phép chạy cờ giới hạn nhỏ (`--limit 2` hoặc `--book sa --chapter 1`)** để xác minh luồng tải và kết quả bóc tách JSON.
> 3. Sau khi kiểm thử mẫu thành công, AI Agent cung cấp câu lệnh CLI đầy đủ để **User chủ động kích hoạt trong cửa sổ Terminal riêng**, đảm bảo kiểm soát tiến độ và dừng/tiếp tục (`Ctrl+C` / `--resume`) an toàn.

---

## 2. Kiến Trúc Lõi `CrawlerCore` (`crawl_factory/core/`)

Mọi nguồn dữ liệu trong `fukuin_hoclieu/crawl_factory/sources/` đều kế thừa từ bộ khung `CrawlerCore` gồm 4 thành phần chuẩn:

```text
fukuin_hoclieu/crawl_factory/
├── config.json                     # Cấu hình tập trung (rate-limit, timeout, headers, paths)
├── core/
│   ├── http_client.py              # Session HTTP có retry, exponential backoff, jitter & анти-CF check
│   ├── state_manager.py            # Đọc/ghi nguyên tử (atomic write) vào state/*.json + xử lý Ctrl+C
│   ├── text_normalizer.py          # Chuẩn hóa Unicode NFC, sửa lỗi Eth Ð (U+00D0), sửa Double-UTF8
│   └── usfm_books.py               # Bảng hằng số chuẩn 66 sách (USFM <-> httlvn <-> tinlanh <-> getbible)
├── state/                          # Lưu checkpoint tiến độ (cho phép resume tức thì khi ngắt giữa chừng)
├── raw/                            # Lưu nguyên bản HTML / XML / USFM / JSON tải về (Immutable Cache)
└── sources/
    ├── docs/                       # Tài liệu đặc tả kỹ thuật và bẫy runtime của từng nguồn
    ├── kinhthanh_httlvn/           # Crawler & Parser cho kinhthanh.httlvn.org (VI1934)
    ├── tinlanh_com/                # Crawler & Parser cho www.tinlanh.com + 3-way Oracle Diff
    ├── thanhca_httlvn/             # Crawler & Parser cho thanhca.httlvn.org (903 Thánh Ca + 100 KTĐĐ)
    ├── vietchristian/              # Crawler & Parser cho vietchristian.com
    └── open_multilingual/          # Ingestor cho WLC, GNT, WEB, KJV, Kougo-yaku, Bungo-yaku, Sanbika 1954
```

### 2.1. Cơ chế Ghi Nguyên Tử (`Atomic State & Raw Persistence`) & Bắt Tín Hiệu `Ctrl+C`
* **Không bao giờ ghi trực tiếp đè lên file `.json` hoặc `.html` đang mở**:
  - Mọi thao tác lưu file vào `raw/` và `state/*.json` đều ghi ra file tạm `*.tmp` trước, gọi `f.flush()` + `os.fsync()`, sau đó dùng `os.replace(tmp_path, target_path)`.
  - Nhờ đó, dù mất điện hay bấm `Ctrl+C` đúng lúc đang ghi file, file `state/*.json` không bao giờ bị hỏng (corrupted JSON).
* **Xử lý `SIGINT` (`Ctrl+C`) êm ái**:
  - `StateManager` đăng ký `signal.signal(signal.SIGINT, self._handle_sigint)`: khi nhận tín hiệu dừng từ người dùng, crawler hoàn tất nốt bước ghi của item hiện tại, lưu checkpoint vào `state/`, in thống kê tiến độ và thoát sạch với mã `0`.

### 2.2. Điều Tra Chuyên Sâu Về Giới Hạn Theo Thời Gian / Số Trang / Dung Lượng Băng Thông (Time / Page-Window / Bandwidth Quotas)

Qua phân tích HTTP Response Headers, Server Stack và đo đạc dung lượng thực tế (`wire_bytes` vs `uncompressed_bytes`) trên toàn bộ 12 endpoints của dự án, hệ thống ghi nhận **5 Bẫy Giới Hạn Lưu Lượng & Phiên (TRAP F1 – TRAP F5)** mà nếu không xử lý sẽ làm gãy quá trình crawl dài hơi:

#### Bảng Chẩn Đoán Hạ Tầng Server & Dung Lượng Thực Tế Trên Đường Truyền

| Nguồn / Endpoint | Web Server & WAF / Hosting | Kích thước Không Nén | Kích thước Có `gzip` (`wire_bytes`) | Header Phiên / Đặc tính Giới hạn |
|---|---|---|---|---|
| `kinhthanh.httlvn.org` (HTML chương) | `Microsoft-IIS/10.0` (ASP.NET MVC 5.0) | `~68 KB – 145 KB` | **`10.3 KB`** (Giảm **85%**) | `Set-Cookie: versions_used_recent=VI1934` |
| `thanhca.httlvn.org` (`?op=chords`) | `Microsoft-IIS/10.0` (ASP.NET MVC 5.2) | `~28 KB – 42 KB` | **`5.3 KB`** (Giảm **83%**) | `Set-Cookie: thanh-ca_cookie=["1",...]` (**Bẫy phình Cookie!**) |
| `thanhca.httlvn.org` (`/Download/SheetMusic/{id}`) | `Microsoft-IIS/10.0` (Attachment UUID) | `~65 KB – 85 KB` | **`75.4 KB`** (`encoding=none`, **không nén!**) | Tải 650 bài tốn `~48 MB` băng thông thô |
| `www.tinlanh.com` (`.shtml` chương) | **`LiteSpeed` trên `Hostinger (hpanel)`** | `~18 KB – 32 KB` | **`5.2 KB`** (Giảm **78%**) | **Giới hạn cửa sổ trượt (Sliding Window Req Quota)** của Hostinger shared hosting! |
| `vietchristian.com` | **Cloudflare (`CF-RAY`)** + `IIS / PleskWin` | `~35 KB – 485 KB` | **`8.4 KB`** (trang chủ) | `Set-Cookie: ASPSESSIONID...` + Cloudflare `jsd` |
| `api.getbible.net/v2/vietnamese.json` | **Cloudflare** (`cfOrigin;dur=1215ms`) | `13.28 MB` (Trọn bộ 66 sách!) | **`2.07 MB`** (Giảm **84%**) | Tải **1 file duy nhất** thay cho `1.189` request lẻ! |
| `bolls.life/static/translations/JPKJV.json` | `nginx` | `22.37 MB` (Trọn bộ 66 sách!) | **`~5.4 MB`** | Tải **1 file duy nhất** thay cho `1.189` request lẻ! |
| `codeload.github.com` (`morphhb` / `sblgnt`) | GitHub Edge CDN (`japaneast`) | `~14 MB` / `~4 MB` | **`~11 MB` / `~1.5 MB` (`.zip`)** | Tải **2 file `.zip`** thay cho `66` request lẻ! |

---

#### Phân Tích 5 Bẫy Giới Hạn Lưu Lượng (`TRAP F1` – `TRAP F5`) & Cơ Chế Phòng Vệ Trong `PoliteHttpClient`

1. **TRAP F1 — Bẫy Băng Thông Không Nén & Lỗi Giải Nén `gzip` Trong `urllib.request`**:
   - **Hiện tượng**: Nếu không gửi header `Accept-Encoding: gzip, deflate`, tổng dung lượng tải 1.189 chương trên `kinhthanh.httlvn.org` lên tới `~105 MB` (thay vì `12.2 MB`), dễ chạm ngưỡng giới hạn băng thông/IP của nhà mạng hoặc firewall. Nhưng nếu bật `Accept-Encoding: gzip` với thư viện chuẩn `urllib.request` của Python, `urllib` trả về byte nén thô (`0x1f 0x8b`), gọi `.decode("utf-8")` trực tiếp sẽ văng lỗi `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8b`!
   - **Giải pháp đã cài đặt trong [`core/http_client.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py)**: Luôn gửi `Accept-Encoding: gzip, deflate` và tự động kiểm tra header `Content-Encoding` / magic bytes `0x1f 0x8b` để giải nén bằng `gzip.decompress` / `zlib.decompress` trước khi trả về `HttpResponse.body`.

2. **TRAP F2 — Bẫy Phình To Cookie Lịch Sử (`thanh-ca_cookie=["1","2",...]`) Gây Lỗi `HTTP 400 Request Too Long` & Quá Tải DB**:
   - **Hiện tượng**: Trên `thanhca.httlvn.org`, mỗi khi truy cập bài hát số `N`, server trả về `Set-Cookie: thanh-ca_cookie=["1","2",..., "N"]` để hiển thị cột *"Mới truy cập"*. Nếu crawler dùng `CookieJar` tự động lưu và gửi lại cookie này qua 903 bài hát:
     - Sau ~450 bài, kích thước header `Cookie` vượt quá giới hạn `8 KB – 16 KB` của `Microsoft-IIS/10.0`, khiến mọi request tiếp theo bị chặn cứng với lỗi **`HTTP 400 Bad Request - Request Header Too Long`**!
     - Đồng thời, ở mỗi request, server ASP.NET phải truy vấn lại hàng trăm bài trong `thanh-ca_cookie` để render sidebar, làm thời gian phản hồi chậm dần từ `700ms` lên `> 5000ms`!
   - **Giải pháp (Stateless Cookie Hygiene)**: `PoliteHttpClient` không gắn `HTTPCookieProcessor` tự động mà áp dụng **Stateless Cookie Whitelist** — bỏ qua hoàn toàn mọi header `Set-Cookie` từ server (`thanh-ca_cookie`, `versions_used_recent`, `ASPSESSIONID*`), chỉ gửi đúng cookie tĩnh khai báo trong `config.json` (`version_current=VI1934`).

3. **TRAP F3 — Giới Hạn Số Trang Theo Cửa Sổ Trượt (Sliding-Window Page Quota) Trên Hostinger `LiteSpeed` (`tinlanh.com`) & `IIS 10.0` (`*.httlvn.org`)**:
   - **Hiện tượng**:
     - `www.tinlanh.com` chạy trên hạ tầng **Hostinger (`platform: hostinger`, `panel: hpanel`, `Server: LiteSpeed`)**. Các gói hosting dùng chung của Hostinger áp dụng bộ lọc chống cào dữ liệu theo cửa sổ trượt (thường chặn tạm thời IP hoặc trả về `429`/`503`/ngắt kết nối nếu một IP tải liên tục `> 150–250` trang trong vòng 5–10 phút mà không có quãng nghỉ).
     - Tương tự, `Microsoft-IIS/10.0` có module *Dynamic IP Restrictions* theo dõi số request liên tục trên một cửa sổ thời gian.
   - **Giải pháp Kép (Chiến lược "Smart Tie-Breaker" + "Batch Cooldown")**:
     - **Tầng 1 — Triệt tiêu 96% số request vào `tinlanh.com` nhờ `GetBible Bulk` (`2.07 MB`)**: Trong [`sources/tinlanh_com/crawler.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/tinlanh_com/crawler.py), crawler tải trọn bộ 66 sách `GetBible vietnamese.json` chỉ bằng **1 request duy nhất (`2.07 MB` gzip)**, sau đó so khớp cục bộ trong RAM với `kinhthanh_httlvn`. Ở `> 95%` số chương nơi cả 2 nguồn đã khớp tuyệt đối 100% (đạt đa số 2/3), crawler **không cần gửi bất kỳ request nào tới `www.tinlanh.com`**, chỉ gọi `tinlanh.com` ở vài chục chương có sự khác biệt để làm phiếu phân xử thứ 3!
     - **Tầng 2 — Nghỉ theo lô tự động (`Batch Cooldown` & `Macro Cooldown`)**: Trong `PoliteHttpClient`, cứ mỗi `batch_size = 80` trang, crawler tự động dừng nghỉ ngắn `25s – 35s`; và cứ mỗi `macro_batch_size = 300` trang, crawler tự động nghỉ dài `90s – 110s` để xóa sạch bộ đếm cửa sổ trượt trên tường lửa!

4. **TRAP F4 — Giới Hạn Dung Lượng Băng Thông (`/Download/SheetMusic/{id}` Không Nén) & Điều Tốc Thích Nghi AIMD**:
   - **Hiện tượng**: Trên `thanhca.httlvn.org`, endpoint `/Data/thanh-ca/sheet/1.xml` trả về `404` vì file thật trên đĩa được đặt tên theo UUID (`filename=6254cfd8-5c75-4b64-9055-9406b3de5d40`) và bắt buộc phải tải qua controller `/Download/SheetMusic/{id}`. Đáng chú ý, controller này **không bật nén gzip** (`wire_bytes = 75,408 bytes` / bài), khiến việc tải liên tục cả 903 bài kèm XML tiêu tốn `~53 MB` băng thông thô.
   - **Giải pháp**:
     - Tách cờ `--skip-musicxml` trên `run_crawler.py` để có thể tải riêng toàn bộ 903 trang lời + hợp âm chỉ với **`4.8 MB` tổng dung lượng gzip**!
     - Tích hợp bộ **Kiểm soát Ngân sách Băng thông (`max_mb_per_hour = 120 MB/h`)** và thuật toán **Điều tốc Thích nghi AIMD (Additive Increase / Multiplicative Decrease)** trong [`core/http_client.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py): theo dõi trung bình trượt của độ trễ phản hồi (`_recent_latencies_ms`). Ngay khi phát hiện độ trễ server vọt lên `> 3.2x` mức nền (dấu hiệu server bắt đầu bóp băng thông / soft-throttling) hoặc gặp `429`/`503`, `current_delay_seconds` tự động tăng lên gấp đôi và chỉ giảm dần về mức chuẩn sau `15` request nhanh liên tiếp.

5. **TRAP F5 — Xoay Vòng IP Qua Proxy Pool Khi Cần (`ProxyRotator`)**:
   - Tích hợp sẵn lớp [`ProxyRotator`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py#L64-L90) tương thích trực tiếp với định dạng `state/proxy_pool.json` của `LumiLearnWeb_hoclieu` (`--proxy-url` hoặc `--proxy-pool-file`), tự động đổi sang IP tiếp theo nếu gặp `HTTP 403 / 429 / 503`.

---

## 3. Cấu Hình Tập Trung (`crawl_factory/config.json`)

```json
{
  "project": "fukuin_hoclieu",
  "version": "1.0.0",
  "paths": {
    "raw_dir": "raw",
    "state_dir": "state",
    "output_data_dir": "../data"
  },
  "default_headers": {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6"
  },
  "sources": {
    "kinhthanh_httlvn": {
      "base_url": "https://kinhthanh.httlvn.org",
      "bible_version": "VI1934",
      "cookies": {
        "version_current": "VI1934"
      },
      "delay_seconds": 1.2,
      "jitter_seconds": 0.3,
      "timeout_seconds": 20,
      "max_retries": 4,
      "concurrency": 1
    },
    "tinlanh_com": {
      "base_url": "https://www.tinlanh.com",
      "delay_seconds": 0.6,
      "jitter_seconds": 0.2,
      "timeout_seconds": 15,
      "max_retries": 3,
      "concurrency": 1
    },
    "thanhca_httlvn": {
      "base_url": "https://thanhca.httlvn.org",
      "delay_seconds": 1.0,
      "jitter_seconds": 0.3,
      "timeout_seconds": 20,
      "max_retries": 4,
      "concurrency": 1
    },
    "vietchristian": {
      "base_url": "https://vietchristian.com",
      "delay_seconds": 2.5,
      "jitter_seconds": 0.5,
      "timeout_seconds": 25,
      "max_retries": 3,
      "concurrency": 1
    }
  }
}
```

---

## 4. Bảng Tổng Hợp 18 Bẫy Runtime (Master Runtime Trap Matrix)

Đây là danh sách kiểm tra bắt buộc (Mandatory Pre-Flight Checklist) trước khi nghiệm thu bất kỳ bộ parser nào trong `fukuin_hoclieu/crawl_factory`:

| Mã Bẫy | Nguồn dữ liệu | Hiện tượng / Nguy cơ lỗi lúc Runtime | Giải pháp kỹ thuật bắt buộc trong Parser | Tài liệu chi tiết |
|---|---|---|---|---|
| **TRAP A1** | `kinhthanh.httlvn.org` | 6 mã sách trên URL khác với viết tắt thông thường: Ê-xơ-ra là **`exo`** (dễ nhầm `xu`/`exe`), Ê-xơ-tê là **`et`**, Châm-ngôn là **`ch`**, Ô-sê là **`os`**, Phi-líp là **`phi`** còn Phi-lê-môn là **`phil`** (cực dễ tráo sách!), Khải-huyền là **`kh`**. | Dùng cứng bảng hằng số 66 sách đã trích xuất trực tiếp từ `/?v=VI1934`. | [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) |
| **TRAP A2** | `kinhthanh.httlvn.org` | 16 câu khuyết trong Tân Ước (`mat/17:21`...) không có thẻ `<span class="verse">`, văn bản bị nhồi vào `title="...][gt=Có mấy bản cũ thêm..."` của thẻ `<a>⚓</a>` câu trước; đồng thời `][gt=` ở `es/53`, `ro/8` lại chứa địa chỉ tham chiếu chéo! | Tách `title` theo `][gt=` trước khi tách `;`. Phân loại phần sau `][gt=` bằng regex `OMITTED_VERSE_RE` và `REF_ITEM_RE`. | [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) |
| **TRAP A3** | `kinhthanh.httlvn.org` | Mã viết tắt sách trong tooltip `⚓` (`Mac`, `Kh`, `Exe`, `1Co`) khác với chữ thường trên URL. | Chuẩn hóa về mã USFM 3 ký tự qua từ điển `CROSSREF_ABBR_TO_USFM`. | [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) |
| **TRAP A4** | `kinhthanh.httlvn.org` | Thượng đề Thi-thiên nằm trong thẻ `<i>` của `<div class="title">`, bên trong `<i>` lại lồng thẻ `<a title="...">⚓</a>` (`thi/51`). | Tách thẻ `<a>⚓</a>` bên trong `<i>` trước khi lấy chuỗi `psalm_superscription`. | [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) |
| **TRAP A5** | `kinhthanh.httlvn.org` | Ngắt dòng thơ dùng `<br/>&emsp;`, ngắt khổ 8 câu ở `thi/119` dùng `<br/>&emsp;<br/>`, đổi vai đối thoại ở `nha/1` dùng ` --- <br/>&emsp;`. | Bảo toàn cấu trúc dòng thơ `\n` và cờ `is_stanza_break` thay vì `.get_text()` phẳng. | [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) |
| **TRAP A6** | `kinhthanh.httlvn.org` & `thanhca.httlvn.org` | Đường dẫn MP3 trong HTML chứa dấu gạch chéo ngược Windows (`\Audio\VI1934\...` và `\mp3/1.mp3`). | Luôn gọi `.replace("\\", "/")` trên mọi URL media trích xuất từ HTML. | [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md) |
| **TRAP B1** | `Bolls.life JPKJV.json` (`JA_KOUGO`) | Thượng đề Thi-thiên được đánh dấu `[0]` và `[00]` ở đầu `"text"` nhưng bị gán `"verse": 1, 2`, đẩy câu `[1]` thực sự sang `"verse": 3` (lệch `+1` hoặc `+2` câu toàn chương!). | Bắt buộc đọc số câu từ tiền tố `[N]` ở đầu `"text"`, tách `[0]`/`[00]` làm thượng đề và kiểm tra chéo với `GetBible japkougo.json`. | [`multilingual-open-bibles-hymns.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/multilingual-open-bibles-hymns.md) |
| **TRAP B2** | `GetBible vietnamese.json` & `vietchristian.com` | Chữ `Đ` hoa tiếng Việt bị mã hóa bằng ký tự `Ð` (`U+00D0` — Latin Eth) gây trượt tìm kiếm và báo lệch giả khi diff. | Chạy `.replace("\u00d0", "\u0110").replace("\u00f0", "\u0111")` + `NFC` trong `text_normalizer.py`. | [`tinlanh-com.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/tinlanh-com.md) |
| **TRAP B3** | `www.tinlanh.com` | Một số chương có lỗi gạch nối OCR (`Đức-Giê hô-va` tại `thithien23.shtml`). | Dùng thuật toán **Biểu quyết Đa số 2/3 (3-Way Majority Voting)** giữa `kinhthanh_httlvn`, `tinlanh_com` và `getbible_vietnamese`. | [`tinlanh-com.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/tinlanh-com.md) |
| **TRAP C1** | `eBible.org` `engwebp_usfm.zip` (`EN_WEB`) | Mã Strong tự động trong `WEB` USFM bị lỗi nghiêm trọng (`In` và `God` cùng gắn `H8064`), tên file đánh số từ `02-GEN`..`96-REV`, và chú thích `\f...\f*` nằm xen giữa câu. | Bỏ hoàn toàn thuộc tính `strong` của `WEB`; chỉ lấy mã Strong tiếng Anh từ `EN_KJV` (`eng-kjv2006_usfm.zip`), xóa số `0` đầu (`H0430` $\to$ `H430`) và bóc tách `\f...\f*` trước. | [`multilingual-open-bibles-hymns.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/multilingual-open-bibles-hymns.md) |
| **TRAP C2** | `OpenScriptures WLC` (`ORIG_WLC`) | `lemma` không có chữ `"H"` (`lemma="c/d/776"`, `"1254 a"`), chữ Hê-bơ-rơ có dấu `/` phân tách hình thái (`בְּ/רֵאשִׁ֖ית`), và Thi-thiên đánh số thượng đề là câu 1. | Parse `lemma` qua `parse_wlc_lemma()`, xóa `/` khi hiển thị (`surface_display`), và dịch số câu Thi-thiên theo offset thượng đề. | [`multilingual-open-bibles-hymns.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/multilingual-open-bibles-hymns.md) |
| **TRAP C3** | `MorphGNT SBLGNT` (`ORIG_GNT`) | Định dạng 7 cột phẳng (`010101` = Book 01 Mat, Chap 01, Verse 01), không gắn sẵn mã `Gxxxx` trong file `.txt`. | Giải mã địa chỉ `BBCCVV` từ cột 1 và nối (join) cột 7 (`lemma`) với `strongsgreek.xml`. | [`multilingual-open-bibles-hymns.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/multilingual-open-bibles-hymns.md) |
| **TRAP D1** | `vietchristian.com` (`tklk.xml` / `.dat`) | Lỗi Double-Encoded UTF-8 Mojibake (`ThÃ¡nh Kinh LÆ°á»£c Kháº£o`). | Khôi phục bằng `fix_double_utf8()` (`.encode("cp1252").decode("utf-8")`). | [`vietchristian.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/vietchristian.md) |
| **TRAP D3** | `thanhca.httlvn.org` | `<div id="details-content">` không tồn tại trên các tab `mp3`, `beat`, `karaoke`, `ppt`, `sheet`; và thanh tab hiển thị cả 7 tab ngay cả khi bài hát không có media. | Chỉ crawl `?op=chords` (lấy cả lời + hợp âm), lấy danh sách 384 bài có MP3 từ `#audio-player-playlist` của Bài 1, và lọc trước danh sách bài có `beat`/`karaoke` từ `/thanh-ca?op=beat/karaoke`. | [`thanhca-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/thanhca-httlvn.md) |
| **TRAP D4** | `thanhca.httlvn.org` | Tồn tại 2 họ DOM lời bài hát khác nhau (Bài 1 gộp khổ trong `<p>` kèm `<b>B1L</b>`; Bài 42/903 tách từng dòng thành `<p>` kèm `<p><b>Câu 1</b></p>`). | Viết parser hỗ trợ đồng thời cả hai cấu trúc DOM Kiểu A và Kiểu B. | [`thanhca-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/thanhca-httlvn.md) |
| **TRAP D5** | `thanhca.httlvn.org` | Thẻ hợp âm `<i class="chord-group">` nằm giữa từ ghép có gạch nối (`Giê-<i class="chord-group">[Eb]ru</i>-sa-lem`). | Tuyệt đối không chèn khoảng trắng khi unwrap/thay thế thẻ `<i>` và `<span class="hopam">`. | [`thanhca-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/thanhca-httlvn.md) |
| **TRAP D8** | `thanhca.httlvn.org` | Trang `/kinh-thanh-doi-dap` có 2 thẻ `<a>` giống hệt nhau trên mỗi card (trả về 200 link cho 100 bài). | Khử trùng lặp theo `reading_id` (`1..100`) ngay ở bước Discovery. | [`thanhca-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/thanhca-httlvn.md) |
| **TRAP E1** | `Hymnary.org` & `ja.wikisource` | `Hymnary.org` chặn `HTTP 403`; trang `創世記(口語訳)` trên `ja.wikisource` bị treo biển xóa. | Dùng `Bolls.life JPKJV.json` + `GetBible` cho `JA_KOUGO`; dùng `ja.wikipedia` API + `kanichi-sanbika/songs.json` + `ja.wikisource Category:讃美歌` cho `Sanbika 1954`. | [`multilingual-open-bibles-hymns.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/multilingual-open-bibles-hymns.md) |
| **TRAP F1** | Toàn bộ 12 Endpoints | Không bật `gzip` làm dung lượng tăng gấp 6–7 lần (`105 MB` thay vì `12.2 MB`); nhưng bật `gzip` trên `urllib.request` trả về byte nén `0x1f 0x8b` gây lỗi `UnicodeDecodeError`. | Luôn gửi `Accept-Encoding: gzip, deflate` và tự động giải nén bằng `gzip.decompress` / `zlib.decompress` trong `PoliteHttpClient`. | [`core/http_client.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py) |
| **TRAP F2** | `thanhca.httlvn.org` & `vietchristian.com` | Server trả về `Set-Cookie: thanh-ca_cookie=["1","2",...]`; nếu lưu & gửi lại qua 903 bài sẽ vượt giới hạn header 8KB–16KB của IIS (`HTTP 400 Request Too Long`) và làm chậm DB. | Áp dụng **Stateless Cookie Hygiene**: tuyệt đối không lưu/gửi lại cookie lịch sử (`thanh-ca_cookie`, `versions_used_recent`, `ASPSESSIONID*`). | [`core/http_client.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py) |
| **TRAP F3** | `www.tinlanh.com` (Hostinger `LiteSpeed`) & `*.httlvn.org` (`IIS 10.0`) | Giới hạn số trang theo cửa sổ trượt (Sliding Window Page Quota: tải liên tục `> 150–250` trang trong 5–10 phút bị bóp băng thông hoặc chặn tạm thời). | (1) Dùng gói Bulk `GetBible vietnamese.json` (`2.07 MB` gzip = 1 request) để chỉ gọi `tinlanh.com` khi 2 nguồn lệch nhau (**Smart Tie-Breaker**); (2) Tự động nghỉ theo lô `Batch Cooldown` (80 trang nghỉ 30s, 300 trang nghỉ 95s). | [`sources/tinlanh_com/crawler.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/tinlanh_com/crawler.py) |
| **TRAP F4** | `thanhca.httlvn.org` (`/Download/SheetMusic/{id}`) | Endpoint tĩnh `/Data/thanh-ca/sheet/1.xml` trả về `404` (file thật lưu bằng UUID), còn `/Download/SheetMusic/{id}` không nén `gzip` (`75 KB`/bài $\approx 48\text{ MB}$ tổng). | Hỗ trợ cờ `--skip-musicxml`, kiểm soát ngân sách `max_mb_per_hour = 120 MB/h` và tự động điều tốc **AIMD** khi độ trễ server tăng vọt `> 3.2x` mức nền. | [`core/http_client.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py) |
| **TRAP F5** | Mọi nguồn khi bị giới hạn theo IP | Chặn hoặc bóp tốc độ theo địa chỉ IP đơn lẻ khi chạy mạng yếu/nhiều tác vụ. | Tích hợp `ProxyRotator` (`--proxy-url`, `--proxy-pool-file`) tương thích định dạng `state/proxy_pool.json` của `LumiLearnWeb_hoclieu`. | [`core/http_client.py`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/core/http_client.py) |

