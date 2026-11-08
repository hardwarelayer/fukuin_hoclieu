# `www.tinlanh.com` & `GetBible vietnamese.json` — Hệ Thống Đối Chiếu Chéo 3 Nguồn (3-Way Oracle) Cho Bản Truyền Thống 1925

* **Source ID**: `tinlanh_com` & `getbible_vietnamese`
* **Trang gốc**:
  - Nguồn 2 (`tinlanh_com`): `https://www.tinlanh.com/thanhkinh/`
  - Nguồn 3 (`getbible_vietnamese`): `https://api.getbible.net/v2/vietnamese.json` (và `https://api.getbible.net/v2/vietnamese/{book_nr}/{chapter}.json`)
* **Ngày khảo sát & Reverse Engineering**: 08/11/2026
* **Vai trò trong hệ sinh thái `fukuin_hoclieu`**: Tạo thành **Hội đồng Đối chiếu Ba Nguồn Độc lập (3-Way Majority Voting Oracle)** cùng với `kinhthanh_httlvn` nhằm loại bỏ 100% lỗi chính tả số hóa / OCR trong 31.102 câu Kinh Thánh Tiếng Việt 1925, đồng thời cung cấp cấu trúc tham khảo Bài học Kinh Thánh (`/thanhkinh/baihoc/`).

---

## 1. Kiến Trúc Server, URL & Đặc Điểm Kỹ Thuật Của `www.tinlanh.com`

### 1.1. Hạ tầng & Chống Crawl
* **Web Server**: Apache phục vụ các file `.shtml` (Server-Side Includes tĩnh).
* **WAF / Anti-bot**: Không có Cloudflare challenge, không có CAPTCHA, phản hồi cực nhanh (`< 150ms / request`, dung lượng mỗi chương chỉ `6 KB – 25 KB`).
* **Encoding**: UTF-8 chuẩn (dựng sẵn trên HTML tĩnh).
* **Tốc độ crawl an toàn**: `0.5s – 0.8s / request` tuần tự (`1.189` file `.shtml` chỉ tốn ~12 phút tải về `raw/tinlanh_com/`).

### 1.2. Cấu trúc URL Deterministic (1.189 Chương)

| Phân mục | URL Pattern | Ví dụ thực tế | Ghi chú kỹ thuật |
|---|---|---|---|
| Trang chủ Thánh Kinh | `/thanhkinh/` | `https://www.tinlanh.com/thanhkinh/` | Mục lục Cựu Ước & Tân Ước |
| Mục lục Cựu Ước (39 sách) | `/thanhkinh/cuuuoc/` | `https://www.tinlanh.com/thanhkinh/cuuuoc/` | Chứa link tới 39 thư mục sách Cựu Ước |
| Mục lục Tân Ước (27 sách) | `/thanhkinh/tanuoc/` | `https://www.tinlanh.com/thanhkinh/tanuoc/` | Chứa link tới 27 thư mục sách Tân Ước |
| Mục lục chương của 1 sách | `/thanhkinh/{testament}/{tinlanh_slug}/` | `/thanhkinh/cuuuoc/sangtheky/` | `testament` là `cuuuoc` (sách 1–39) hoặc `tanuoc` (sách 40–66) |
| **Trang nội dung 1 chương** | `/thanhkinh/{testament}/{tinlanh_slug}/{tinlanh_slug}{chapter}.shtml` | `/thanhkinh/cuuuoc/sangtheky/sangtheky1.shtml` | URL hoàn toàn tất định theo `tinlanh_slug` (xem bảng 66 sách tại [`kinhthanh-httlvn.md`](file:///c:/HomeWorking/911/repos/fukuin_hoclieu/crawl_factory/sources/docs/kinhthanh-httlvn.md)) |
| Bài học Kinh Thánh | `/thanhkinh/baihoc/{tinlanh_slug}/` | `/thanhkinh/baihoc/mac/` | Các bài học khảo sát Kinh Thánh theo sách |

> [!IMPORTANT]
> **Quy tắc URL cho 5 sách chỉ có 1 chương (`Áp-đia`, `Phi-lê-môn`, `II Giăng`, `III Giăng`, `Giu-đe`)**:
> Trên `www.tinlanh.com`, các sách 1 chương **vẫn có hậu tố số `1`** trước `.shtml`:
> - `/thanhkinh/cuuuoc/apdia/apdia1.shtml`
> - `/thanhkinh/tanuoc/philemon/philemon1.shtml`
> - `/thanhkinh/tanuoc/2giang/2giang1.shtml`
> - `/thanhkinh/tanuoc/3giang/3giang1.shtml`
> - `/thanhkinh/tanuoc/giude/giude1.shtml`

---

## 2. Giải Phẫu DOM `.shtml` & Các Bẫy Runtime Trên `tinlanh.com` + `GetBible`

### 2.1. Mẫu HTML thực tế trên `www.tinlanh.com` (`/thanhkinh/cuuuoc/sangtheky/sangtheky1.shtml`)

```html
<div class="crum">
  <span class="bread">
    <a href="/">Trang Bìa</a> > <a href="/thanhkinh/">Thánh Kinh</a> >
    <a href="/thanhkinh/cuuuoc/">Kinh Thánh Cựu Ước</a> >
    <a href="/thanhkinh/cuuuoc/sangtheky/">Sáng-thế Ký</a> > Sáng-thế Ký 1
  </span>
</div>
<br><br>
<b> Sáng-thế Ký 1</b><br>
1 Ban đầu Đức Chúa Trời dựng nên trời đất.<br>
2 Vả, đất là vô hình và trống không, sự mờ tối ở trên mặt vực; Thần Đức Chúa Trời vận hành trên mặt nước. <br>
3 Đức Chúa Trời phán rằng: Phải có sự sáng; thì có sự sáng. <br>
```

* **Cách bóc tách (`parse_tinlanh_shtml`)**:
  - Tìm thẻ `<b>` chứa tên sách và số chương (ví dụ `<b> Sáng-thế Ký 1</b><br>`).
  - Toàn bộ các dòng tiếp theo cho tới `<div` hoặc `<hr` hoặc cuối container có định dạng:
    `^\s*(\d+)\s+(.+?)\s*<br\s*/?>`
  - Không có thẻ `<span>` riêng cho từng câu mà mỗi câu là một dòng text thuần kết thúc bằng `<br>`.

### 2.2. Ba "Bẫy Dữ Liệu" (Runtime Traps) Phát Hiện Qua Kiểm Thử Thực Nghiệm

#### Bẫy B1 — Lỗi Dấu Gạch Nối OCR Trên `www.tinlanh.com` (`Đức-Giê hô-va`)
* Khi kiểm thử thực tế `/thanhkinh/cuuuoc/thithien/thithien23.shtml` (Thi-thiên 23:1), văn bản trên `tinlanh.com` trả về:
  `1 Đức-Giê hô-va là Đấng chăn giữ tôi; tôi sẽ chẳng thiếu thốn gì.`
* Trong khi đó, cả `kinhthanh.httlvn.org` và `GetBible vietnamese.json` đều trả về đúng chuẩn chính tả Bản 1925:
  `Đức Giê-hô-va là Đấng chăn giữ tôi: tôi sẽ chẳng thiếu thốn gì.` (chú ý dấu gạch nối nằm ở `Giê-hô-va` chứ không phải `Đức-Giê`, và dấu `:` sau chữ `tôi`).
* **Hệ quả**: Không bao giờ dùng `tinlanh.com` ghi đè mù quáng lên `kinhthanh.httlvn.org`; chỉ dùng `tinlanh.com` kết hợp với `GetBible vietnamese.json` trong thuật toán Biểu quyết Đa số 2/3!

#### Bẫy B2 — Ký Tự `Ð` (`U+00D0` Latin Capital Letter Eth) Trong `GetBible vietnamese.json`
* Khi kiểm thử trực tiếp `https://api.getbible.net/v2/vietnamese/40/17.json` (Ma-thi-ơ 17) và `19/23.json` (Thi-thiên 23), dữ liệu JSON của `GetBible` dùng ký tự **`Ð` (`U+00D0` — chữ Eth tiếng Iceland/Tây Âu)** thay cho chữ **`Đ` (`U+0110` — chữ Đ tiếng Việt chuẩn Unicode)**, đồng thời đôi chỗ có ký tự `ð` (`U+00F0`)!
* **Quy tắc chuẩn hóa bắt buộc trước khi so khớp hoặc lưu trữ**:
  ```python
  import unicodedata

  def normalize_vietnamese_1925(text: str) -> str:
      if not text:
          return ""
      # 1. Đưa về chuẩn Unicode NFC
      text = unicodedata.normalize("NFC", text)
      # 2. Thay thế ký tự Eth (U+00D0 / U+00F0) bằng chữ Đ/đ chuẩn Việt ngữ (U+0110 / U+0111)
      text = text.replace("\u00d0", "\u0110").replace("\u00f0", "\u0111")
      # 3. Chuẩn hóa khoảng trắng
      text = re.sub(r"[ \t\u00a0]+", " ", text).strip()
      return text
  ```
  Nếu thiếu bước `.replace("\u00d0", "\u0110")`, phép so sánh chuỗi giữa `kinhthanh_httlvn` (`Đức`) và `getbible_vietnamese` (`Ðức`) sẽ báo lệch giả (False Positive Diff) trên hàng chục ngàn câu!

#### Bẫy B3 — Sự Khác Biệt Ở 16 Câu Khuyết Tân Ước Giữa 3 Nguồn
* Kiểm thử tại `Ma-thi-ơ 17:21` trên cả 3 nguồn:
  1. **`kinhthanh.httlvn.org` (`mat/17`)**: Chỉ có **26 thẻ `<span class="verse">`** (khuyết `mat_17_21`, nội dung câu 21 nằm trong `][gt=` của thẻ `<a>⚓</a>` cuối câu 20).
  2. **`www.tinlanh.com` (`mathio17.shtml`)**: Cũng khuyết câu 21 hoặc để trống.
  3. **`GetBible vietnamese.json` (`/v2/vietnamese/40/17.json`)**: Có đầy đủ **27 phần tử JSON** trong mảng `verses`, trong đó phần tử thứ 21 là:
     `{"chapter": 17, "verse": 21, "name": "Matthew 17:21", "text": "Nhưng thứ quỉ nầy nếu không cầu nguyện và không kiêng ăn thì chẳng trừ nó được."}`
* **Quy tắc hợp nhất hoàn hảo**:
  - Nhờ `GetBible vietnamese.json` và phần bóc tách `][gt=` từ `kinhthanh.httlvn.org`, `fukuin_hoclieu` có đầy đủ văn bản tiếng Việt của cả 16 câu này!
  - Trong file JSON xuất bản ra `fukuin`, các câu này vẫn có mặt đúng thứ tự số câu (`verse: 21`) để không làm gãy liên kết đối chiếu 1-1 với bản `KJV` và `Bungo-yaku`, kèm theo thuộc tính `"critical_text_status": "bracketed_footnote"` để giao diện hiển thị trong ngoặc vuông `[...]` kèm ghi chú *"Có mấy bản cổ thêm câu này"*.

---

## 3. Thuật Toán Biểu Quyết Đa Số 2/3 (`diff_bible_1925.py`)

```python
from difflib import SequenceMatcher

def resolve_verse_3way(v_httlvn: str, v_tinlanh: str, v_getbible: str, verse_id: str):
    """
    Đối chiếu 3 nguồn độc lập của Bản Truyền Thống 1925:
    - Nguồn A (Primary): kinhthanh.httlvn.org (giữ nguyên cấu trúc dòng thơ \n)
    - Nguồn B (Secondary): www.tinlanh.com
    - Nguồn C (Tertiary): api.getbible.net/v2/vietnamese.json
    """
    a_flat = normalize_vietnamese_1925(v_httlvn.replace("\n", " "))
    b_flat = normalize_vietnamese_1925(v_tinlanh)
    c_flat = normalize_vietnamese_1925(v_getbible)

    # Trường hợp 1: Cả 3 nguồn khớp tuyệt đối 100%
    if a_flat == b_flat == c_flat:
        return {"status": "UNANIMOUS_3_OF_3", "chosen": v_httlvn, "diff_log": None}

    # Trường hợp 2: kinhthanh_httlvn khớp với ít nhất 1 trong 2 nguồn đối chiếu (2/3 Majority)
    if a_flat == b_flat or a_flat == c_flat:
        return {"status": "MAJORITY_HTTLVN_2_OF_3", "chosen": v_httlvn, "diff_log": None}

    # Trường hợp 3: tinlanh_com và getbible khớp nhau, còn kinhthanh_httlvn khác biệt
    if b_flat == c_flat and a_flat != b_flat:
        return {
            "status": "OVERRIDE_BY_TINLANH_GETBIBLE_2_OF_3",
            "chosen": b_flat,
            "diff_log": {"verse_id": verse_id, "httlvn": a_flat, "consensus": b_flat},
        }

    # Trường hợp 4: Cả 3 khác nhau (thường chỉ khác dấu chấm câu : vs ; hoặc hoa/thường)
    # Giữ v_httlvn làm gốc nhưng xuất ra state/bible_1925_3way_discrepancies.json để kiểm tra
    return {
        "status": "NEEDS_REVIEW_ALL_3_DIFFER",
        "chosen": v_httlvn,
        "diff_log": {
            "verse_id": verse_id,
            "httlvn": a_flat,
            "tinlanh": b_flat,
            "getbible": c_flat,
        },
    }
```

---

## 4. Quy Trình Pipeline & File Trạng Thái (`state/tinlanh_com_state.json`)

* `--step 1` (**Download `getbible_vietnamese`**): Tải trọn gói 1 file duy nhất `https://api.getbible.net/v2/vietnamese.json` (`~4.8 MB`) lưu vào `raw/getbible/vietnamese.json`.
* `--step 2` (**Fetch `tinlanh_com` `.shtml`**): Duyệt 1.189 chương theo bảng ánh xạ `tinlanh_slug`, tải về `raw/tinlanh_com/{testament}/{tinlanh_slug}/{tinlanh_slug}{chapter}.shtml` với checkpoint trong `state/tinlanh_com_state.json`.
* `--step 3` (**Run 3-Way Verification**): Chạy `diff_bible_1925.py` trên toàn bộ 31.102 câu, xuất báo cáo kiểm định `state/bible_1925_verification_report.json` và danh sách các câu khác biệt `state/bible_1925_3way_discrepancies.json`.
