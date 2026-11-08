# `bible.com` (YouVersion) — Khảo Sát Các Bản Dịch Tiếng Việt & Bản Quyền

* **Source ID**: `bible_com`
* **Trang gốc**: [https://www.bible.com/vi](https://www.bible.com/vi) · [Danh mục bản tiếng Việt](https://www.bible.com/vi/languages/vie)
* **Ngày khảo sát**: 08/11/2026
* **Vai trò**: Nguồn chuẩn hóa mã sách quốc tế (**USFM 3.0**: `GEN`, `EXO`, ..., `REV`), xác minh tình trạng pháp lý/bản quyền của toàn bộ 7 bản dịch tiếng Việt, và tham khảo cấu trúc **Verse of the Day** + **Reading Plans**.

---

## 1. Bảng 7 Bản Dịch Tiếng Việt Trên `bible.com/vi/languages/vie`

Qua khảo sát trực tiếp từng trang phiên bản trên `bible.com`, hiện có **7 bản dịch tiếng Việt** với thông tin đơn vị phát hành và bản quyền như sau:

| Version ID (YouVersion) | Mã viết tắt | Tên đầy đủ | Đơn vị sở hữu / Xuất bản | Tình trạng Bản quyền | Chính sách trên `fukuin` |
|-------------------------|-------------|------------|--------------------------|----------------------|--------------------------|
| **`193`** | **`VIE1925`** | Kinh Thánh Tiếng Việt 1925 | Bible Society Vietnam / United Bible Societies | **Public Domain** (Xuất bản 1925/1926, >95 năm) | ✅ **Sử dụng toàn văn** (tương đương bản `VI1934` trên `httlvn.org`) |
| **`151`** | **`VIE2010`** | Kinh Thánh Tiếng Việt Bản Hiệu Đính 2010 | Bible Society Vietnam (Hội Kinh Thánh Việt Nam) | © 2010 United Bible Societies. Bảo hộ bản quyền | ❌ Không đăng toàn văn; chỉ dẫn link tham khảo |
| **`19`** | **`BD2011`** | Kinh Thánh Tiếng Việt, Bản Dịch 2011 | Rev. Dr. Bau Dang (MS TS Đặng Ngọc Báu) | *"Property of Rev. Dr. Bau Dang. All rights reserved."* | ❌ Không đăng toàn văn |
| **`449`** | **`NVB`** | Kinh Thánh Bản Dịch Mới (New Vietnamese Bible) | Vietnamese Bible, INC. (Ủy ban 10 nhà thần học dịch từ BHS 1984 & UBS Greek) | © Vietnamese Bible, INC. Bảo hộ bản quyền | ❌ Không đăng toàn văn |
| **`205`** | **`BPT`** | Thánh Kinh Bản Phổ Thông | Biblica / World Bible Translation Center | © World Bible Translation Center. Bảo hộ bản quyền | ❌ Không đăng toàn văn |
| **`1638`** | **`KTHD`** | Kinh Thánh Hiện Đại | Hội Kinh Thánh / Đối tác phát hành | Bảo hộ bản quyền | ❌ Không đăng toàn văn |
| **`4916`** | **`FHB-VI`** | Kinh Thánh Tấm Lòng Của Cha (Father's Heart Bible) | Father's Heart Ministry | Bảo hộ bản quyền | ❌ Không đăng toàn văn |

> [!IMPORTANT]
> **Kết luận pháp lý cốt lõi từ khảo sát `bible.com`**:
> Toàn bộ các bản dịch mới từ năm 1990 trở lại đây (`VIE2010`/`RVV11`, `BD2011`, `NVB`, `BPT`, `KTHD`, `FHB-VI`) đều ghi rõ quyền sở hữu trí tuệ của tổ chức hoặc cá nhân dịch thuật. Do đó, dự án `fukuin` (website nội dung tĩnh hoàn toàn miễn phí) **chỉ sử dụng toàn văn Bản Truyền Thống 1925 (`VIE1925` / `VI1934`)** làm gốc dữ liệu.

---

## 2. Cấu Trúc URL & Khai Thác Metadata Từ `bible.com`

YouVersion sử dụng Next.js App Router:
- Trang danh mục bản dịch: `/vi/versions/{id}-{slug}`
- Trang đọc chương: `/vi/bible/{version_id}/{USFM_BOOK}.{chapter}.{VERSION_CODE}` (ví dụ `/vi/bible/193/GEN.1.VIE1925`)
- Trang câu gốc trong ngày: `/vi/verse-of-the-day`
- Trang kế hoạch đọc: `/vi/reading-plans`

### Những gì `crawl_factory` thu thập từ `bible.com`:
1. **Bảng ánh xạ chuẩn 66 mã sách USFM (`GEN` $\rightarrow$ `REV`)**:
   - Ghép mã nội bộ của `kinhthanh.httlvn.org` (`sa`, `xu`, `le`, ...) và `tinlanh.com` (`sangtheky`, `xuatediptoky`, ...) về chuẩn quốc tế USFM 3 chữ cái (`GEN`, `EXO`, `LEV`, ...). Nhờ mã USFM chuẩn này, `fukuin` có thể dễ dàng ghép thêm văn bản tiếng Anh Public Domain (`KJV`, `WEB`, `ASV`) hoặc bản gốc Hy Lạp/Hê-bơ-rơ (Strong's Concordance) về sau mà không lệch bất kỳ câu nào.
2. **Danh sách câu gốc tiêu biểu từ `/vi/verse-of-the-day`**:
   - Chỉ lấy **địa chỉ câu Kinh Thánh** (ví dụ `JER.29.11`, `PHP.4.13`, `ISA.41.10`, `PSA.23.1`), sau đó trích xuất nội dung văn bản từ kho `VI1934` nội bộ của ta để tạo kho **365 Daily Quotes (Câu Gốc Hằng Ngày)**.

