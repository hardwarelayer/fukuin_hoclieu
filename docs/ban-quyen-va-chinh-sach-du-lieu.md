# Điều Tra Bản Quyền & Chính Sách Sử Dụng Dữ Liệu (`fukuin_hoclieu`)

> **Tài liệu này giải đáp trực tiếp câu hỏi trọng tâm của dự án:**
> *"Kinh Thánh (bản dịch cũ, hiện có bản mới, nhưng không rõ bản quyền sao), Thánh Ca, Kinh Thánh Đối Đáp — dữ liệu nào được phép xuất bản miễn phí 100% lên các trang tĩnh của `fukuin`, và dữ liệu nào cần giới hạn?"*

---

## 1. Bản Quyền Các Bản Dịch Kinh Thánh Tiếng Việt

Qua khảo sát đối chiếu trên `kinhthanh.httlvn.org` và `bible.com/vi/languages/vie`, các bản dịch Kinh Thánh tiếng Việt (Tin Lành) hiện chia thành **2 nhóm pháp lý hoàn toàn khác biệt**:

### 1.1. Bản Dịch Thuộc Phạm Vi Công Cộng (Public Domain) — **AN TOÀN 100% ĐỂ XUẤT BẢN TOÀN VĂN**

| Mã bản dịch | Tên gọi phổ biến | Lịch sử & Năm xuất bản | Tình trạng pháp lý |
|-------------|------------------|------------------------|--------------------|
| **`VI1934` / `VIE1925` / `BTT 1925`** | **Kinh Thánh Bản Truyền Thống (1925 / 1926)** | Dịch bởi Ủy ban dịch thuật gồm các giáo sĩ Hội Truyền Giáo Phúc Âm Liên Hiệp (C&MA: W.C. Cadman, Grace Cadman, J.D. Olsen, H.A. Jackson...) và học giả **Phan Khôi**, xuất bản lần đầu tại Hà Nội năm **1925–1926** (Thánh Kinh Hội phát hành, in lại năm 1934). | **Phạm vi công cộng (Public Domain)** trên toàn cầu (đã xuất bản trên 100 năm kể từ 1925/1926). Không chịu bất kỳ hạn chế bản quyền nào. |

* **Chính sách trên `fukuin`**:
  * Được phép đăng tải **toàn văn 66 sách (1.189 chương, 31.102 câu)** trên các trang HTML tĩnh.
  * Được phép tách lẻ từng câu để làm **Trang SEO trích dẫn câu gốc**, **Thẻ ảnh chia sẻ (Quote Cards)**, **Bài tập điền từ khuyết**, **Trắc nghiệm (Quiz)** và **Kinh Thánh Đối Đáp**.
  * **Lưu ý biên tập**: Giữ nguyên văn phong trang trọng cổ điển của bản 1925; có thể kèm chú thích từ vựng cổ (*Từ điển từ cổ Kinh Thánh 1925*: ví dụ *“sự sáng”*, *“khoảng không”*, *“chẳng hề”*, *“đặng”*, *“nhứt”*, *“Ê-díp-tô” = Ai Cập*, *“thầy tế lễ cả” = thượng tế*) ngay bên dưới câu để người đọc trẻ dễ hiểu mà không vi phạm bản quyền của các bản dịch mới!

---

### 1.2. Các Bản Dịch Mới Đang Bảo Hộ Bản Quyền — **KHÔNG ĐĂNG TOÀN VĂN LÊN SITE TĨNH**

| Mã bản dịch | Tên đầy đủ | Chủ sở hữu Bản quyền (Theo `bible.com`) | Quy định sử dụng thông thường |
|-------------|------------|-----------------------------------------|-------------------------------|
| **`RVV11` / `VIE2010`** | Kinh Thánh Bản Truyền Thống Hiệu Đính 2010 | **United Bible Societies (UBS) / Hội Kinh Thánh Việt Nam (BSV)** | Bản quyền © 2010. Thông lệ của UBS chỉ cho phép trích dẫn ngắn (thường $\le 250$–$500$ câu, không quá $25\%$ tác phẩm và không trọn 1 sách) kèm ghi nguồn; **cấm** sao chép toàn bộ cơ sở dữ liệu lên website thứ ba khi chưa có giấy phép bằng văn bản. |
| **`BD2011`** | Kinh Thánh Tiếng Việt Bản Dịch 2011 | **Rev. Dr. Bau Dang (MS TS Đặng Ngọc Báu)** | Ghi rõ trên `bible.com`: *"Property of Rev. Dr. Bau Dang. All rights reserved."* |
| **`NVB`** | Kinh Thánh Bản Dịch Mới (New Vietnamese Bible) | **Vietnamese Bible, INC.** (Ủy ban 10 nhà thần học dịch từ BHS 1984 & UBS Greek) | Bản quyền thuộc Vietnamese Bible, INC. Cấm nhân bản toàn văn. |
| **`BPT`** | Thánh Kinh Bản Phổ Thông (1998–2010) | **World Bible Translation Center (WBTC) / Biblica / Bible League International** | Bản quyền thương mại/phi lợi nhuận có điều kiện cấp phép riêng. |
| **`BDY`** | Kinh Thánh Bản Diễn Ý | **Living Bibles International / Biblica** | Đang trong thời hạn bảo hộ bản quyền. |
| **`KTHD`** | Kinh Thánh Hiện Đại | **Hội Kinh Thánh / Đối tác phát hành** | Đang trong thời hạn bảo hộ bản quyền. |

> [!WARNING]
> **Quyết định Kiến trúc Pháp lý & Chiến lược Tạo Giá Trị Độc Bản cho `fukuin`:**
> 1. **Chấp nhận dứt khoát không sử dụng các bản hiệu đính có bản quyền (`RVV11`/`VIE2010`, `BD2011`, `NVB`, `BPT`, `BDY`, `KTHD`)**.
> 2. Thay vào đó, `fukuin` tạo ra **sức mạnh riêng vượt trội** mà các trang chỉ đăng văn bản đơn thuần không có được:
>    - **Đối chiếu 6 văn bản Public Domain Đa Ngữ trên từng câu**:
>      - Tiếng Việt: **Bản Truyền Thống 1925 (`VI1934`)**.
>      - Tiếng Anh: **World English Bible (`EN_WEB` — hiện đại, dễ hiểu)** & **King James Version (`EN_KJV` — cổ điển, gắn mã Strong)**.
>      - Tiếng Nhật: **口語訳 1955 (`JA_KOUGO` — hiện đại)** & **文語訳 1917 (`JA_BUNGO` — văn ngôn cổ điển giàu từ Hán-Nhật)**.
>      - Nguyên bản gốc: **Hê-bơ-rơ (`ORIG_WLC` Cựu Ước)** & **Hy Lạp (`ORIG_GNT` Tân Ước)** kèm từ điển gốc **Strong's Concordance (`H1..H8674`, `G1..G5624`)**.
>    - **Lớp Chú Giải Từ Cổ 1925 & Học Chéo Ngôn Ngữ (`hoctamquoc` / `LumiLearnWeb`)**: Giải nghĩa từ cổ bản 1925, hiển thị Furigana, âm Hán-Việt và liên kết tra từ 1-chạm.
>    - **Tách riêng các Đoạn Kinh Thánh Nổi Tiếng & 60 Câu Chuyện Kinh Thánh Minh Họa Bút Chì**: Tạo các trang chuyên đề có chiều sâu biên tập và thẩm mỹ tranh vẽ chì độc quyền.
>    - **Tích hợp Trợ năng `ops_sources/kannert` cho Người Cao Tuổi**: Phóng chữ lớn, thước dẫn dòng, hộp tập trung dòng đọc và đọc giọng nói.

---

## 2. Bản Quyền Thánh Ca (`thanhca.httlvn.org` — 903 Bài)

Bộ 903 bài Thánh Ca trên `thanhca.httlvn.org` gồm hai tầng tác quyền cần phân biệt rõ:

### 2.1. Nhạc và Lời gốc Quốc tế (Đa số 500+ bài đầu)
* Phần lớn các bài Thánh Ca truyền thống (từ bài 1 đến khoảng bài 500+) là các bài Thánh Ca kinh điển thế giới từ thế kỷ 17–đầu thế kỷ 20:
  * Nhạc sĩ / Tác giả lời: *Charles Wesley (1707–1788), Isaac Watts (1674–1748), Fanny J. Crosby (1820–1915), Felice de Giardini (1716–1796), Philip P. Bliss (1838–1876), William J. Kirkpatrick (1838–1921), A.B. Simpson (1843–1919)...*
  * **Tình trạng pháp lý**: Toàn bộ giai điệu gốc, hòa âm cổ điển (4 bè SATB) và lời tiếng Anh gốc của nhóm này đều thuộc **Phạm vi công cộng (Public Domain)**.
  * Các bản dịch lời tiếng Việt đời đầu (trong quyển *Thánh Ca* xuất bản thập niên 1920–1950 của Hội Thánh Tin Lành Việt Nam) đã lưu hành công cộng trong sinh hoạt tôn giáo gần một thế kỷ.

### 2.2. Các Bài Thánh Ca Sáng Tác Mới / Dịch Mới (Đặc biệt phần Biệt Thánh Ca / Bổ sung từ bài ~504–903)
* Có một số bài do các nhạc sĩ, mục sư người Việt sáng tác trong nửa cuối thế kỷ 20 và đầu thế kỷ 21 (ví dụ nhóm *Việt Nam Ca*, *Thanh Niên*, *Biệt Lễ Ca*).
* **Chính sách an toàn trên `fukuin`**:
  1. **Ghi công đầy đủ (Strict Attribution)**: Luôn hiển thị trang trọng tên Nhạc sĩ sáng tác, Dịch giả lời và Năm sáng tác ở đầu trang từng bài Thánh Ca.
  2. **Không sao chép file MP3 thu âm thương mại vào kho Git**: Không tải hàng loạt file MP3 của ca sĩ về phát hành lại. Đối với nhạc nghe/karaoke, chỉ dùng trình nhúng YouTube chính thức (`<iframe>`) hoặc liên kết trực tiếp tới nguồn công khai của Tổng Liên Hội, kèm cơ chế phát MIDI/WebAudio tự động từ dữ liệu nốt nhạc `MusicXML` ngay trên trình duyệt!
  3. **Cơ chế Takedown thân thiện**: Có thông báo rõ ràng ở chân trang: dự án phi lợi nhuận phục vụ tra cứu và thờ phượng; nếu tác giả hoặc đại diện bản quyền của bất kỳ bài Thánh Ca đương đại nào không muốn hiển thị lời/hợp âm, dự án sẽ gỡ bài đó ngay lập tức qua cấu hình `exclude_hymns.json`.

---

## 3. Bản Quyền Kinh Thánh Đối Đáp (100 Bài)

* Toàn bộ **100 bài Kinh Thánh Đối Đáp** (`/kinh-thanh-doi-dap-1` đến `100` trên `thanhca.httlvn.org` và `ktdd.txt` trên `vietchristian.com`) là các câu trích nguyên văn từ **Kinh Thánh Bản Truyền Thống 1925 (`VI1934`)**, sắp xếp xen kẽ câu lẻ (Người hướng dẫn) và câu chẵn (Hội chúng) dùng chung trong nghi thức thờ phượng Tin Lành từ trước năm 1950.
* **Tình trạng pháp lý**: **An toàn 100%** để chuẩn hóa, liên kết chéo với từng câu Kinh Thánh gốc và xuất bản toàn văn trên `fukuin`.

---

## 4. Tóm Tắt Bảng Quyết Định Xuất Bản (`publish_policy`)

| Hạng mục dữ liệu | Chính sách trên `fukuin` | Ghi chú thực thi |
|------------------|--------------------------|------------------|
| Kinh Thánh `VI1934` (Bản 1925) | ✅ **Xuất bản 100% toàn văn** | Kèm từ điển giải nghĩa từ cổ & tên riêng do `fukuin` tự biên soạn |
| Kinh Thánh Tiếng Anh `EN_WEB` & `EN_KJV` | ✅ **Xuất bản 100% toàn văn** | `WEB` (Public Domain/CC0 hiện đại) + `KJV` (1769 Public Domain kèm mã Strong) |
| Kinh Thánh Tiếng Nhật `JA_KOUGO` (1955) & `JA_BUNGO` (1917) | ✅ **Xuất bản 100% toàn văn** | Public Domain tại Nhật Bản; tách từ sẵn kèm Furigana, âm Hán-Việt & link `LumiLearnWeb` |
| Kinh Thánh Nguyên Bản `ORIG_WLC` (Hê-bơ-rơ) & `ORIG_GNT` (Hy Lạp) | ✅ **Xuất bản 100% toàn văn** | Kèm từ điển gốc Strong (`H1..H8674`, `G1..G5624`) để tra nghĩa gốc từng từ |
| Kinh Thánh mới (`RVV11`, `BD2011`, `NVB`, `BPT`...) | ❌ **Không xuất bản văn bản** | Chỉ liệt kê giới thiệu lịch sử bản dịch & dẫn link sang trang chính chủ |
| 100 Bài Kinh Thánh Đối Đáp | ✅ **Xuất bản 100% toàn văn** | Trích từ bản 1925, gắn link 2 chiều về chương/câu Kinh Thánh |
| 903 Bài Thánh Ca Việt + Thánh Ca Nhật `SANBIKA_1954` | ✅ **Xuất bản kèm ghi danh tác giả** | Đối chiếu lời Việt – Anh gốc – Nhật (*Sanbika 1954* Public Domain); hỗ trợ Transpose & Sheet |
| 60 Câu Chuyện Kinh Thánh + Minh Họa Bút Chì | ✅ **Tác phẩm biên soạn & minh họa độc quyền** | Kể chuyện đa ngữ + tranh vẽ chì cổ điển (Content-Addressed Media) |
| Đoạn Kinh Thánh Nổi Tiếng, Daily Quotes, Ngày Này Năm Xưa, Quiz | ✅ **Biên soạn Original trên nền 6 bản Public Domain** | Tối ưu Programmatic SEO & học chéo ngôn ngữ |

