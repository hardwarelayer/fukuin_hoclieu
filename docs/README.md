# `fukuin_hoclieu` — Tài Liệu Kho Dữ Liệu Kinh Thánh & Thánh Ca Tiếng Việt

> **Điểm vào tài liệu của kho dữ liệu `fukuin_hoclieu`.**
> Kho dữ liệu này cung cấp toàn bộ học liệu tĩnh đã chuẩn hóa, kiểm thử toàn vẹn 2 chiều và rà soát bản quyền cho ứng dụng web **[fukuin](../../fukuin/docs/README.md)**.
> Kế thừa trực tiếp triết lý thiết kế dữ liệu đồ thị hai chiều của [RoTK9_hoclieu](../../RoTK9_hoclieu/docs/SoT.md) và quy trình pipeline của [LumiLearnWeb_hoclieu](../../LumiLearnWeb_hoclieu/docs/README.md).

---

## 1. Mục Lục Tài Liệu

| Tài liệu | Nội dung trọng tâm |
|----------|--------------------|
| **[SoT.md](./SoT.md)** | **Single Source of Truth (SoT)**: Tầm nhìn, kiến trúc dữ liệu tổng thể, đồ thị liên kết đa chiều và lộ trình phát triển học liệu `fukuin_hoclieu` |
| **[ban-quyen-va-chinh-sach-du-lieu.md](./ban-quyen-va-chinh-sach-du-lieu.md)** | **Phân tích Pháp lý & Bản quyền**: Lý giải chi tiết tình trạng bản quyền các bản dịch Kinh Thánh tiếng Việt (1925 vs 2010/2011/NVB/BPT), Thánh Ca, KTĐĐ và ranh giới xuất bản an toàn $100\%$ |
| **[kien-truc-hoc-lieu-va-schema.md](./kien-truc-hoc-lieu-va-schema.md)** | **Đặc tả Schema JSON & Cổng Kiểm (`validate_hoclieu.py`)**: Định nghĩa chi tiết từng thực thể dữ liệu đa ngôn ngữ (Việt, Anh, Nhật, Hê-bơ-rơ/Hy Lạp) trong `data/` và quy tắc kiểm thử tự động |
| **[cau-chuyen-kinh-thanh-va-minh-hoa-but-chi.md](./cau-chuyen-kinh-thanh-va-minh-hoa-but-chi.md)** | **Câu chuyện Kinh Thánh & Minh họa Bút chì**: Kiến trúc 60 câu chuyện Kinh Thánh kinh điển, pipeline tranh vẽ chì cổ điển (Content-Addressed Media) và kết nối từ vựng đa ngữ |
| **[du-lieu-hoi-thanh-va-ban-do-lich-su.md](./du-lieu-hoi-thanh-va-ban-do-lich-su.md)** | **Dữ liệu Hội Thánh (VN & JP), Bản Đồ Lịch Sử & Tìm Kiếm Nhanh Buổi Nhóm**: Schema danh bạ Hội Thánh do Ban biên tập duyệt, lưới bản đồ tương thích engine `tamquocchi` (`map-svg.js`) và bảng lệnh tắt `worship_aliases.json` |
| **[sheet-music-omr-midi-abc-pipeline.md](./sheet-music-omr-midi-abc-pipeline.md)** | **Pháp Lý Bản Quyền Sheet Nhạc, Giải Mã Ảnh (OMR) & Chưng Cất `.abc` / `.mid` 4 Bè SATB**: Phân tích 3 lớp bản quyền sheet nhạc, kiến trúc `music_sheet_distiller.py` và pipeline OMR (`Audiveris` / `homr`) |
| **[../crawl_factory/sources/docs/README.md](../crawl_factory/sources/docs/README.md)** | **Tài liệu Crawl Factory (5 nguồn Việt + Kho Đa Ngữ Mở)**: Khảo sát kỹ thuật `kinhthanh.httlvn.org`, `thanhca.httlvn.org`, `vietchristian.com`, `bible.com`, `www.tinlanh.com` & nguồn mở Hê-bơ-rơ/Hy Lạp/Anh/Nhật |
| **[../crawl_factory/sources/docs/technical-design-and-anti-blocking.md](../crawl_factory/sources/docs/technical-design-and-anti-blocking.md)** | **Thiết kế Kỹ thuật Lõi Crawler & Ma trận 23 Bẫy Runtime**: Kiến trúc `CrawlerCore`, checkpoint `state/`, `config.json`, chống chặn và bảng kiểm tra 23 bẫy runtime (`TRAP A1` – `TRAP F5`) |
| **[../crawl_factory/sources/docs/multilingual-open-bibles-hymns.md](../crawl_factory/sources/docs/multilingual-open-bibles-hymns.md)** | **Nguồn Mở Đa Ngữ**: Đặc tả `WLC` (Hê-bơ-rơ), `GNT` (Hy Lạp + Strong's), `WEB` & `KJV` (Anh), `口語訳 1955` & `文語訳 1917` (Nhật) và `讃美歌 1954` (Thánh Ca Nhật) |
| **[../crawl_factory/sources/docs/distill-contract.md](../crawl_factory/sources/docs/distill-contract.md)** | **Hợp đồng Chưng cất (`distill`)**: Quy tắc chuyển dữ liệu từ `crawl_factory/` sang `data/` và `fukuin` |

---

## 2. Cấu Trúc Thư Mục Của Kho `fukuin_hoclieu`

```text
fukuin_hoclieu/
├── README.md                           # Tổng quan kho học liệu & lệnh chạy nhanh
├── docs/                               # Tài liệu kiến trúc dữ liệu, bản quyền & schema
│   ├── README.md                       # Mục lục tài liệu (file này)
│   ├── SoT.md                          # Single Source of Truth
│   ├── ban-quyen-va-chinh-sach-du-lieu.md
│   ├── kien-truc-hoc-lieu-va-schema.md
│   ├── cau-chuyen-kinh-thanh-va-minh-hoa-but-chi.md
│   └── du-lieu-hoi-thanh-va-ban-do-lich-su.md
├── crawl_factory/                      # Nhà máy thu thập & chuẩn hóa thô theo nguồn
│   ├── church_submissions/             # Hồ sơ Hội Thánh do người dùng đóng góp chờ Ban biên tập duyệt
│   └── sources/
│       └── docs/                       # Đặc tả kỹ thuật từng nguồn & hợp đồng distill
│           ├── README.md
│           ├── kinhthanh-httlvn.md
│           ├── thanhca-httlvn.md
│           ├── vietchristian.md
│           ├── bible-com.md
│           ├── tinlanh-com.md
│           ├── multilingual-open-bibles-hymns.md
│           └── distill-contract.md
├── tools/                              # Pipeline chưng cất, đối chiếu & kiểm thử (Python)
│   ├── diff_bible_1925.py              # Đối chiếu 1-1 Kinh Thánh 1925 giữa HTTLVN và TinLanh.com
│   ├── align_multilang_bibles.py       # Gióng hàng 6 bản: VI1934 + WEB + KJV + Kougo + Bungo + WLC/GNT
│   ├── ingest_church_submission.py     # Công cụ Ban biên tập duyệt thông tin Hội Thánh & gắn tọa độ bản đồ
│   ├── build_hoclieu.py                # Tổng hợp toàn bộ JSON chuẩn hóa vào data/
│   └── validate_hoclieu.py             # Quality Gate kiểm tra toàn vẹn đồ thị 2 chiều
└── data/                               # Kho JSON Hoàn Chỉnh (Đầu vào cho web app fukuin)
    ├── manifest.json                   # Metadata, số lượng bản ghi & chữ ký SHA-256
    ├── bible/                          # 66 sách, 1.189 chương (VI1934 + WEB + KJV + JA Kougo/Bungo + WLC/GNT)
    ├── lexicon/                        # Từ điển gốc Strong's Hebrew/Greek + Cầu nối từ vựng LumiLearnWeb (JA/EN/Hán-Việt)
    ├── stories/                        # 60 Câu chuyện Kinh Thánh kèm manifest minh họa bút chì (Pencil Sketch)
    ├── churches/                       # Danh bạ & tọa độ các Hội Thánh tại Việt Nam (churches_vn.json) & Nhật Bản (churches_jp.json)
    ├── maps/                           # Lưới bản đồ vẽ tay SVG & Tuyến hành trình truyền giáo lịch sử (engine tamquocchi)
    ├── search/                         # Chỉ mục lệnh mở nhanh buổi nhóm (worship_aliases.json: Thánh Ca, KTĐĐ, Sách đoạn:câu)
    ├── hymns/                          # 903 bài Thánh Ca Việt + đối chiếu lời Anh & Thánh Ca Nhật (Sanbika 1954)
    ├── ktdd/                           # 100 bài Kinh Thánh Đối Đáp
    ├── quotes/                         # Các đoạn Kinh Thánh nổi tiếng, 366 Daily Quotes & Câu gốc theo tâm trạng
    ├── history/                        # Ngày này năm xưa (Lịch sử Hội Thánh & Tin Lành VN)
    ├── plans/                          # Lịch đọc Kinh Thánh nguyên năm (4 lộ trình)
    ├── quizzes/                        # Ngân hàng câu hỏi Đố Kinh Thánh & bài tập đa ngữ
    └── entities/                       # Từ điển Nhân vật, Địa danh & Khái niệm Kinh Thánh
```

