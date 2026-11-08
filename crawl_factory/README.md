# `fukuin_hoclieu/crawl_factory` — Sổ Tay Kỹ Thuật & Hướng Dẫn Vận Hành Cho Đội Dự Án

Tài liệu này là **Sổ tay vận hành trực tiếp (Developer & Operator Runbook)** dành cho đội ngũ kỹ sư phát triển và bảo trì hệ thống thu thập, đối chiếu và chuẩn hóa dữ liệu của `fukuin_hoclieu`.

---

## 1. Cấu Trúc Thư Mục Mã Nguồn (`crawl_factory/`)

```text
fukuin_hoclieu/crawl_factory/
├── README.md                           # Sổ tay vận hành cho đội dự án (file này)
├── config.json                         # Cấu hình trung tâm (delay, jitter, timeout, retries, endpoints)
├── run_crawler.py                      # Điểm vào CLI duy nhất để điều phối toàn bộ 5 nguồn dữ liệu
├── core/                               # Khung lõi (Core Framework) dùng chung — 0 phụ thuộc ngoài
│   ├── __init__.py
│   ├── usfm_books.py                   # Bảng chuẩn hóa 66 sách Kinh Thánh đa nguồn (USFM <-> HTTLVN <-> TinLanh <-> WLC/GNT)
│   ├── text_normalizer.py              # Chuẩn hóa Unicode NFC, sửa lỗi Eth Ð (U+00D0), khôi phục Double-UTF8, chuẩn hóa URL media
│   ├── state_manager.py                # Ghi file nguyên tử (.tmp -> os.replace) & xử lý dừng an toàn Ctrl+C (SIGINT)
│   └── http_client.py                  # Polite HTTP Client (rate-limit, jitter, exponential backoff, kiểm tra chữ ký DOM & chống CF)
├── sources/                            # Các module Crawler & Parser độc lập theo từng nguồn
│   ├── docs/                           # Tài liệu Reverse-Engineering & Đặc tả 18 Bẫy Runtime
│   │   ├── README.md
│   │   ├── technical-design-and-anti-blocking.md   # Thiết kế lõi & Bảng kiểm tra 18 Bẫy Runtime (TRAP A1 - E1)
│   │   ├── kinhthanh-httlvn.md                     # Đặc tả kinhthanh.httlvn.org (VI1934)
│   │   ├── tinlanh-com.md                          # Đặc tả www.tinlanh.com & 3-Way Majority Voting Oracle
│   │   ├── thanhca-httlvn.md                       # Đặc tả thanhca.httlvn.org (903 Thánh Ca & 100 KTĐĐ)
│   │   ├── vietchristian.md                        # Đặc tả vietchristian.com (7 request tĩnh)
│   │   ├── multilingual-open-bibles-hymns.md       # Đặc tả WLC, GNT, WEB, KJV, Kougo-yaku, Bungo-yaku, Sanbika 1954
│   │   ├── bible-com.md                            # Ranh giới bản quyền các bản dịch mới
│   │   └── distill-contract.md                     # Hợp đồng chưng cất dữ liệu sang data/
│   ├── kinhthanh_httlvn/               # Nguồn 1: Kinh Thánh VI1934 (1.189 chương)
│   │   ├── crawler.py
│   │   └── parser.py
│   ├── tinlanh_com/                    # Nguồn 2: Đối chiếu 3 nguồn (tinlanh.com + GetBible + HTTLVN)
│   │   ├── crawler.py
│   │   └── parser.py
│   ├── thanhca_httlvn/                 # Nguồn 3: 903 bài Thánh Ca & 100 bài Kinh Thánh Đối Đáp
│   │   ├── crawler.py
│   │   └── parser.py
│   ├── vietchristian/                  # Nguồn 4: Dưỡng Linh, tên Tiếng Anh Thánh Ca, KTĐĐ/Thánh Ca text
│   │   ├── crawler.py
│   │   └── parser.py
│   └── open_multilingual/              # Nguồn 5: Đa ngữ mở (JA_KOUGO Ruby, JA_BUNGO, ORIG_WLC, ORIG_GNT, Sanbika)
│       ├── ingestor.py
│       └── parsers.py
├── state/                              # Tự động sinh: Lưu trạng thái tiến độ từng chương/bài (checkpoint resume)
├── raw/                                # Tự động sinh: Cache bất biến lưu nguyên bản HTML/XML/JSON tải về
└── normalized/                         # Tự động sinh: JSON trung gian đã xử lý sạch 18 bẫy runtime
```

---

## 2. Nguyên Tắc Bất Di Bất Dịch Dành Cho Team Đi Sau

1. **Không tự đoán mã sách hay cấu trúc HTML — Luôn đọc Bảng 18 Bẫy Runtime trước**:
   - Trước khi chỉnh sửa bất kỳ parser nào, hãy đọc [`sources/docs/technical-design-and-anti-blocking.md`](./sources/docs/technical-design-and-anti-blocking.md).
   - Toàn bộ 18 bẫy thực tế (như 6 mã sách URL `exo`, `et`, `ch`, `os`, `phi`/`phil`, `kh` trên `kinhthanh.httlvn.org`; câu 21 khuyết nằm trong `][gt=` của câu 20 ở `mat/17`; lệch số câu `[0]`/`[00]` ở sách Thi-thiên của `Bolls.life JPKJV.json`; hay lỗi chữ `Ð` `U+00D0` Eth) đều đã được giải quyết trong code và kiểm tra tự động trong `tools/validate_hoclieu.py`.
2. **Luôn dùng `atomic_write_*` khi ghi file**:
   - Mọi thao tác ghi vào `raw/`, `state/`, `normalized/`, `data/` bắt buộc gọi `atomic_write_json` / `atomic_write_text` / `atomic_write_bytes` trong [`core/state_manager.py`](./core/state_manager.py).
3. **An toàn khi dừng giữa chừng (`Ctrl+C`) và chạy tiếp (`Resume`)**:
   - Khi đang chạy crawl ở Bước 2 (`--step 2`), nếu cần dừng máy, chỉ cần nhấn **`Ctrl+C` một lần**. `StateManager` sẽ đợi tải xong chương hiện tại, lưu file `state/{source}_state.json` rồi thoát sạch. Khi chạy lại cùng câu lệnh, những chương đã có trạng thái `"fetched"` hoặc `"parsed"` sẽ tự động được bỏ qua.

---

## 3. Hướng Dẫn Chạy Từng Nguồn (CLI Cheat Sheet)

Mọi câu lệnh đều chạy từ thư mục gốc `c:\HomeWorking\911\repos\fukuin_hoclieu` với cờ `python -X utf8`:

### 3.1. Kiểm thử nhanh (Smoke Test với `--limit` hoặc `--book` / `--chapter`)
```powershell
cd C:\HomeWorking\911\repos\fukuin_hoclieu

# 1. Tải & parse thử Ma-thi-ơ chương 17 (kiểm tra bẫy câu 21 khuyết nằm trong ][gt=) và Thi-thiên 51 (thượng đề <i>)
python -X utf8 crawl_factory\run_crawler.py --source kinhthanh_httlvn --step all --book MAT --chapter 17
python -X utf8 crawl_factory\run_crawler.py --source kinhthanh_httlvn --step all --book PSA --chapter 51

# 2. Tải & đối chiếu 3 nguồn (HTTLVN vs TinLanh.com vs GetBible) cho Thi-thiên 23
python -X utf8 crawl_factory\run_crawler.py --source kinhthanh_httlvn --step all --book PSA --chapter 23
python -X utf8 crawl_factory\run_crawler.py --source tinlanh_com --step all --book PSA --chapter 23

# 3. Tải & parse đa ngôn ngữ (Tiếng Nhật 口語訳 có Ruby + 文語訳 + Hê-bơ-rơ WLC) cho Sáng-thế Ký 1 và Thi-thiên 51
python -X utf8 crawl_factory\run_crawler.py --source open_multilingual --step all --book GEN --chapter 1
python -X utf8 crawl_factory\run_crawler.py --source open_multilingual --step all --book PSA --chapter 51

# 4. Tải & parse thử 2 bài Thánh Ca đầu tiên (+ lấy luôn danh sách 384 bài có MP3 và mục lục 100 bài KTĐĐ)
python -X utf8 crawl_factory\run_crawler.py --source thanhca_httlvn --step all --limit 2

# 5. Chưng cất sang thư mục data/ và chạy Cổng kiểm thử toàn vẹn 2 chiều
python -X utf8 tools\build_hoclieu.py
python -X utf8 tools\validate_hoclieu.py
```

### 3.2. Chạy thu thập toàn bộ dữ liệu (Full Production Crawl — Chạy trong Terminal riêng)
```powershell
cd C:\HomeWorking\911\repos\fukuin_hoclieu

# Bước A: Toàn văn 1.189 chương Kinh Thánh Bản 1925 (~25 phút)
python -X utf8 crawl_factory\run_crawler.py --source kinhthanh_httlvn --step all

# Bước B: Đối chiếu 3 nguồn trên toàn bộ 1.189 chương (~15 phút)
python -X utf8 crawl_factory\run_crawler.py --source tinlanh_com --step all

# Bước C: Toàn bộ 903 bài Thánh Ca + MusicXML + 100 bài Kinh Thánh Đối Đáp (~25 phút)
python -X utf8 crawl_factory\run_crawler.py --source thanhca_httlvn --step all

# Bước D: 7 tài nguyên tĩnh từ VietChristian (~20 giây)
python -X utf8 crawl_factory\run_crawler.py --source vietchristian --step all

# Bước E: Đa ngôn ngữ mở (Kougo-yaku Ruby, Bungo-yaku, WLC, MorphGNT, Sanbika 1954)
python -X utf8 crawl_factory\run_crawler.py --source open_multilingual --step all

# Bước F: Build kho dữ liệu data/ & Kiểm định chất lượng 100%
python -X utf8 tools\build_hoclieu.py
python -X utf8 tools\validate_hoclieu.py
```

