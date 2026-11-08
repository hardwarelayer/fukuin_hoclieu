# Hợp Đồng Chưng Cất Dữ Liệu (`crawl_factory` $\rightarrow$ `fukuin_hoclieu/data` $\rightarrow$ `fukuin`)

> **Tài liệu hợp đồng giữa hai kho (`fukuin_hoclieu` và `fukuin`).**
> Kế thừa mô hình của [RoTK9_hoclieu/crawl_factory/docs/distill.md](../../../../RoTK9_hoclieu/crawl_factory/docs/distill.md).
> Kho thô trong `crawl_factory/` mang cờ `publish_to_site: false` trong `manifest.json`: **tuyệt đối không copy nguyên tệp từ `crawl_factory/` lên site `fukuin`**. Web app `fukuin` chỉ đọc dữ liệu đã qua bước chưng cất, đối chiếu và kiểm duyệt bản quyền tại `fukuin_hoclieu/data/`.

---

## 1. Bảng Phân Định Ranh Giới Hai Kho

| Hạng mục | Đường dẫn | Vai trò | Được đưa lên HTML `fukuin`? |
|----------|-----------|---------|-----------------------------|
| Kho crawl thô | `fukuin_hoclieu/crawl_factory/raw/` | Lưu HTML/TXT/XML tải từ 5 nguồn (bị `.gitignore` nếu nặng) | **Không bao giờ** |
| Bản bóc tách theo nguồn | `fukuin_hoclieu/crawl_factory/normalized/` | JSONL chuẩn hóa từng nguồn riêng biệt | **Không trực tiếp** |
| Script chưng cất & đối chiếu | `fukuin_hoclieu/tools/` | Ghép khóa USFM, diff câu Kinh Thánh 1925, lọc bản quyền | — |
| **Kho Học Liệu Chuẩn Hóa** | `fukuin_hoclieu/data/` | Single Source of Truth đã vượt qua `validate_hoclieu.py` | **Có** (qua `prepare_site.py`) |
| Dữ liệu sinh tĩnh cho Web | `fukuin/src/data/generated/` | Các tệp JSON đã chia trang, tạo slug và gắn liên kết 2 chiều | **Có** (đầu vào của Astro build) |

---

## 2. Hệ Thống Khóa Chuẩn Hóa Toàn Cục (Canonical Keys)

Mọi nguồn dữ liệu khi đi qua bước `distill` phải quy về bộ 4 khóa chuẩn sau để liên kết 2 chiều không bao giờ bị đứt:

### 2.1. Khóa Sách, Chương & Câu Kinh Thánh (`book_id`, `chapter_id`, `verse_uid`)
Không dùng mã viết tắt cục bộ của từng trang (`sa` của HTTLVN hay `sangtheky` của TinLanh.com) làm khóa chính, mà dùng **Mã USFM 3 chữ cái chuẩn quốc tế** kết hợp slug tiếng Việt chuẩn:
- `book_id`: Mã USFM viết hoa (`GEN`, `EXO`, `LEV`, ..., `MAT`, `MRK`, `LUK`, `JHN`, ..., `REV`) kèm số thứ tự `book_order` (`1`..`66`).
- `book_slug`: Slug tiếng Việt không dấu chuẩn SEO (`sang-the-ky`, `xuat-e-dip-to-ky`, ..., `giang`, `khai-huyen`).
- `chapter_uid`: `{BOOK_ID}.{CHAPTER}` (ví dụ `GEN.1`, `PSA.23`, `JHN.3`).
- `verse_uid`: `{BOOK_ID}.{CHAPTER}.{VERSE}` (ví dụ `GEN.1.1`, `JHN.3.16`).
- **Quy tắc chuyển đổi tham chiếu chéo (`⚓`)**:
  Khi bóc tách thuộc tính `title="2Co 4:6; Gi 1:1-3"` từ `kinhthanh_httlvn` hoặc `data-bible="sa 1:1-6"` từ `thanhca_httlvn`, bộ parser phải ánh xạ bảng viết tắt tiếng Việt (`sa` $\rightarrow$ `GEN`, `2co` $\rightarrow$ `2CO`, `gi` $\rightarrow$ `JHN`, `1phi` $\rightarrow$ `1PE`) về đúng `verse_uid` chuẩn. Mọi tham chiếu không phân giải được phải bị chặn tại cổng kiểm `validate_hoclieu.py`.

### 2.2. Khóa Thánh Ca (`hymn_uid`)
- Định dạng: `tc:{3_digit_number}` (ví dụ `tc:001` đến `tc:903` cho bộ Thánh Ca Truyền Thống & Biệt Thánh Ca trên `thanhca.httlvn.org`).
- Slug chuẩn trên web: `/thanh-ca/{number}-{slug}` (ví dụ `/thanh-ca/1-cui-xin-vua-thanh-ngu-lai`).

### 2.3. Khóa Kinh Thánh Đối Đáp (`ktdd_uid`)
- Định dạng: `ktdd:{3_digit_number}` (`ktdd:001` đến `ktdd:100`).
- Mỗi phân đoạn trong bài Kinh Thánh Đối Đáp có mảng `source_passages: [{ "label": "Sáng-thế ký 1:1-6", "chapter_uid": "GEN.1", "verse_start": 1, "verse_end": 6 }]` nối ngược về đúng chương và câu Kinh Thánh.

---

## 3. Quy Tắc Đối Chiếu & Lọc Bản Quyền (Distillation Rules)

| Loại dữ liệu | Quy tắc xử lý trong bước `distill` |
|--------------|------------------------------------|
| **Văn bản Kinh Thánh 1925 (`VI1934`)** | Đối chiếu 3 nguồn độc lập (**Biểu quyết 2/3 — 2-of-3 Majority Voting**) giữa `kinhthanh_httlvn`, `tinlanh_com` và `getbible/v2/vietnamese.json`. Tách riêng chú thích văn bản ẩn sau `][gt=` trong thẻ `<a>⚓</a>` và thượng đề Thi-thiên (`<i>` trong `<div class="title">`). Bảo toàn ngắt dòng thơ (`<br/>&emsp;`) trong các sách Thơ ca. |
| **Ma trận 6 Văn bản Đối chiếu Đa Ngữ (`VI1934`, `EN_WEB`, `EN_KJV`, `JA_KOUGO`, `JA_BUNGO`, `ORIG_WLC`/`ORIG_GNT`)** | Xử lý chuẩn xác **16 câu khuyết trong Tân Ước** của bản 1925/Critical Text so với `KJV` (ví dụ `MAT.17.21`: giữ slot câu 21 với nội dung từ chú thích `gt=` của bản 1925 kèm đối chiếu `KJV`/`WEB` để không bao giờ bị lệch số câu!). Xử lý lệch số câu Thi-thiên giữa bản Hê-bơ-rơ (`WLC` tính thượng đề là câu 1) và bản Việt/Anh/Nhật qua `versification_map.json`. |
| **Tokenization & Học liệu Chéo Ngôn ngữ (`LumiLearnWeb` & `hoctamquoc` Bridge)** | Tận dụng trực tiếp thẻ Ruby có sẵn trong `bolls.life/static/translations/JPKJV.json` (`<i>Kanji</i><sup>,reading</sup>`) kết hợp SudachiPy/MeCab cho `JA_BUNGO` và `SANBIKA_1954` để sinh mảng `ja_tokens` chính xác 100% theo ngữ cảnh Kinh Thánh (ví dụ `神` $\rightarrow$ `かみ`, `主` $\rightarrow$ `しゅ`), gắn âm Hán-Việt và khóa `lex_jp_*` / `kanji_*`. |
| **Các bản dịch Kinh Thánh mới (`RVV11`, `BD2011`, `NVB`, `BPT`...)** | **KHÔNG đưa vào `fukuin_hoclieu/data/`**. Bù đắp hoàn toàn bằng sức mạnh đối chiếu 6 bản Public Domain đa ngữ, giải nghĩa từ gốc Hê-bơ-rơ/Hy Lạp, chú giải từ cổ 1925 và tách các **Đoạn Kinh Thánh Nổi Tiếng (`famous_passages.json`)**. |
| **Lời & Hợp âm Thánh Ca (`tc:001`..`tc:903`) + Thánh Ca Nhật (`SANBIKA_1954`)** | Chuẩn hóa lời ca theo từng câu (`stanzas[]`) và điệp khúc (`chorus`). Dòng hợp âm lưu ở định dạng ChordPro chuẩn (`[G]Cúi xin Vua [C]Thánh`). Khớp nối các bài Thánh Ca kinh điển với lời tiếng Anh gốc và lời tiếng Nhật trong **讃美歌 1954 (`SANBIKA_1954`)** thông qua tên gốc (`title_en`) và điệu nhạc (`tune_name`). |
| **Tác giả & Năm sáng tác Thánh Ca** | Tách rõ `composer` (nhạc), `lyricist` (lời gốc/dịch giả) và `year`. Gắn cờ `is_public_domain_music: true` cho các bài trước 1928. |
| **Sheet nhạc (`MusicXML`) & Audio (`MP3`)** | Không nhúng file nhị phân nặng vào Git repo code của `fukuin`. Lưu URL nguồn (`audio_url`, `youtube_beat_id`, `youtube_karaoke_id`) hoặc đẩy MusicXML đã nén nhẹ lên Cloudflare R2 theo mô hình của `LumiLearnWeb`. |
| **Kinh Thánh Đối Đáp (`ktdd:001`..`ktdd:100`)** | Hợp nhất từ `thanhca_httlvn` và đối chiếu với `vietchristian` (`ktdd.txt`). Chuẩn hóa từng lượt đọc thành mảng `turns: [{ "role": "leader" \| "congregation", "text": "..." }]`. |
| **Câu Gốc Theo Chủ Đề / Tâm Trạng & Daily Quotes** | Chỉ lấy danh sách địa chỉ câu gốc (`verse_uid`) và chủ đề từ `vietchristian` (`Dưỡng Linh`) + `bible_com` (`Verse of the Day`), sau đó nạp toàn bộ nội dung chữ từ bản `VI1934` nội bộ và tự biên soạn lời suy ngẫm/giới thiệu ngắn độc lập. |

