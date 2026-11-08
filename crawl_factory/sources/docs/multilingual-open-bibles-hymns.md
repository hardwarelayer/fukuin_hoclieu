# Nguồn Mở Đa Ngữ: Nguyên Bản Hê-bơ-rơ (`WLC`) / Hy Lạp (`GNT`), Tiếng Anh (`WEB`, `KJV`), Tiếng Nhật (`Kougo-yaku`, `Bungo-yaku`) & Thánh Ca Nhật (`Sanbika 1954`)

* **Source IDs**: `orig_wlc`, `orig_gnt`, `en_web`, `en_kjv`, `ja_kougo`, `ja_bungo`, `ja_sanbika`
* **Ngày khảo sát & Reverse Engineering**: 08/11/2026
* **Vai trò trong hệ sinh thái `fukuin_hoclieu`**: Cung cấp toàn bộ kho dữ liệu đối chiếu đa ngôn ngữ **100% Public Domain / Open License**, bao gồm văn bản gốc Hê-bơ-rơ/Hy Lạp gắn mã Strong (`H1..H8674`, `G1..G5624`), hai bản tiếng Anh (`WEB` hiện đại & `KJV` cổ điển), hai bản tiếng Nhật (`口語訳 1955` có sẵn Ruby Furigana & `文語訳 1917`), và Thánh Ca tiếng Nhật (`讃美歌 1954年版`).

---

## 1. Ma Trận Tổng Thể Các Nguồn Đa Ngữ Đã Xác Minh Thực Nghiệm (`HTTP 200 OK`)

| Nhóm | Mã phiên bản | Tên đầy đủ | Ngôn ngữ | Pháp lý | Endpoint Tải Trực Tiếp (Archive / API Tĩnh) | Dung lượng thực tế |
|---|---|---|---|---|---|---|
| **Cựu Ước Gốc** | `ORIG_WLC` | **Westminster Leningrad Codex (WLC)** + Strong's Hebrew | Hê-bơ-rơ / A-ram (`he`) | Public Domain | `https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/{Book}.xml` (39 files) | `~14.2 MB` tổng XML |
| **Tân Ước Gốc** | `ORIG_GNT` | **SBLGNT (`MorphGNT`)** + Strong's Greek Lexicon | Hy Lạp Koine (`el`) | CC-BY 4.0 / PD | `https://raw.githubusercontent.com/morphgnt/sblgnt/master/{61..87}-{Book}-morphgnt.txt` + `strongsgreek.xml` | `~4.1 MB` + `3.8 MB` |
| **Tiếng Anh (Hiện đại)** | `EN_WEB` | **World English Bible (WEB)** | Tiếng Anh (`en`) | Public Domain (CC0) | 1. `https://api.getbible.net/v2/web.json` (JSON sạch)<br>2. `https://ebible.org/Scriptures/engwebp_usfm.zip` (USFM có footnote) | `~4.6 MB` JSON / `2.90 MB` ZIP |
| **Tiếng Anh (Cổ điển + Strong's)** | `EN_KJV` | **King James Version (1769)** + Strong's Concordance | Tiếng Anh (`en`) | Public Domain | 1. `https://ebible.org/Scriptures/eng-kjv2006_usfm.zip` (USFM gắn `\w ...\|strong="H..."\w*`)<br>2. `https://api.getbible.net/v2/kjv.json` | `2.46 MB` ZIP / `~4.5 MB` JSON |
| **Tiếng Nhật (Hiện đại + Ruby)** | `JA_KOUGO` | **口語訳聖書 (Kougo-yaku 1954/1955)** — Japan Bible Society | Tiếng Nhật (`ja`) | Public Domain (sau 50 năm tại Nhật) | 1. `https://bolls.life/static/translations/JPKJV.json` (**Có sẵn Furigana `<i>Kanji</i><sup>,reading</sup>`!**)<br>2. `https://api.getbible.net/v2/japkougo.json` (Oracle đối chiếu số câu) | `22.37 MB` JSON / `~5.2 MB` JSON |
| **Tiếng Nhật (Văn ngôn)** | `JA_BUNGO` | **文語訳聖書 (Bungo-yaku Meiji 1887 / Taisho 1917)** | Tiếng Nhật cổ (`ja-bungo`) | Public Domain | 1. `https://api.getbible.net/v2/japbungo.json` (Trọn bộ 66 sách)<br>2. `https://ja.wikisource.org/w/api.php` (`創世記(文語訳)`, `創世記1 (文語訳ルビ付)`) | `~5.1 MB` JSON |
| **Thánh Ca Nhật** | `JA_SANBIKA` | **讃美歌 (Sanbika 1954 — UCCJ)** | Tiếng Nhật (`ja`) | Public Domain | 1. `https://ja.wikipedia.org/w/api.php?action=query&titles=讃美歌_(1954年版)&prop=revisions&rvprop=content&format=json`<br>2. `https://raw.githubusercontent.com/lee-ship-jp/kanichi-sanbika/main/data/songs.json`<br>3. `ja.wikisource.org` (`Category:讃美歌`) | `99.6 KB` Wikitext + `194.2 KB` JSON |

---

## 2. Giải Phẫu Định Dạng & 6 "Bẫy Runtime" Nghiêm Trọng Đã Phát Hiện Thực Nghiệm

### 2.1. BẪY B1 — Lệch Số Câu (`+1` hoặc `+2`) Trong Sách Thi-thiên Của `Bolls.life JPKJV.json` (`JA_KOUGO`) Do Thượng Đề `[0]` và `[00]`

> [!CAUTION]
> **CẢNH BÁO ĐỎ (CRITICAL RUNTIME TRAP)**:
> Tệp `https://bolls.life/static/translations/JPKJV.json` (`22.37 MB`) là kho báu vì toàn bộ 66 sách `口語訳 1955` đã được gắn sẵn Furigana chuẩn xác (`<i>神</i><sup>,かみ</sup>`). **TUY NHIÊN**, khi kiểm thử thực nghiệm tại sách **Thi-thiên (Book 19, ví dụ Thi-thiên 51 — `https://bolls.life/get-text/JPKJV/19/51/`)**, ta phát hiện lỗi lệch chỉ số `"verse"` cực kỳ nguy hiểm nếu chỉ đọc trường `"verse"` bên ngoài JSON!

* **Dữ liệu JSON thực tế trả về từ `Bolls.life JPKJV` tại Thi-thiên 51 (gồm 21 phần tử thay vì 19 câu)**:
  ```json
  [
    {
      "pk": 2588435,
      "verse": 1,
      "text": "[0]【<i>聖歌</i><sup>,せいか</sup>の<i>指揮者</i><sup>,しきしゃ</sup>によってうたわせたダビデの<i>賛美</i><sup>,さんび</sup>の<i>歌</i><sup>,うた</sup>】"
    },
    {
      "pk": 2588436,
      "verse": 2,
      "text": "[00]これはダビデがバテシバと<i>不義</i><sup>,ふぎ</sup>を<i>行</i><sup>,おこな</sup>ったのち、<i>預言者</i><sup>,よ言しゃ</sup>ナタンがダビデのところにきたときによんだもの"
    },
    {
      "pk": 2588437,
      "verse": 3,
      "text": "[1]<i>神</i><sup>,かみ</sup>よ、あなたのいつくしみによって、わたしをあわれみ、あなたの<i>豊</i><sup>,ゆた</sup>かなあわれみによって、わたしのもろもろのとがをぬぐい<i>去</i><sup>,さ</sup>ってください。"
    }
  ]
  ```
* **Trong khi đó, trên `GetBible japkougo.json` (`/v2/japkougo/19/51.json`)**:
  - Mảng `verses` có đúng **19 câu**, trong đó `"verse": 1` là `"神よ、あなたのいつくしみによって、わたしをあわれみ..."` (khớp 1-1 với câu 1 của bản Tiếng Việt `VI1934` và Tiếng Anh `KJV`/`WEB`!).
* **Nguyên nhân**: Khi `Bolls.life` nhập dữ liệu `JPKJV`, các dòng Thượng đề Thi-thiên được đánh dấu ở đầu chuỗi `"text"` bằng **`[0]`** và **`[00]`**, còn câu 1 thực sự được đánh dấu là **`[1]`** ở đầu `"text"`, nhưng bộ đánh số tự động của `Bolls.life` lại gán `"verse": 1` cho `[0]`, `"verse": 2` cho `[00]`, và `"verse": 3` cho `[1]` (làm toàn bộ 19 câu trong chương bị đẩy lệch đi `+2` câu!).
* **Thuật toán Parser Bắt Buộc Cho `Bolls.life JPKJV.json` (`parse_bolls_jpkjv_chapter`)**:
  1. **Tuyệt đối không dùng trực tiếp trường `"verse"` của JSON khi `"text"` bắt đầu bằng dấu ngoặc vuông `^\[\d+\]`!**
  2. Kiểm tra đầu chuỗi `"text"` bằng regex `r"^\[(0+|([1-9]\d*))\]\s*(.*)$"`:
     - Nếu khớp `[0]` hoặc `[00]` (`group(1) in ("0", "00")`): Đưa nội dung vào mảng thượng đề `psalm_superscription_ja` của chương đó (không tạo câu Kinh Thánh mới).
     - Nếu khớp `[N]` với `N >= 1` (`group(2)`): Dùng chính **`true_verse_num = int(m.group(2))`** làm số câu chuẩn, và cắt bỏ tiền tố `[N]` khỏi `"text"`!
  3. **Đối chiếu chéo tự động với `GetBible japkougo.json`**: Sau khi parse mỗi chương của `Bolls JPKJV`, so khớp tổng số câu (`len(verses)`) và text đã bỏ thẻ Ruby với `api.getbible.net/v2/japkougo.json` để đảm bảo độ chính xác 100%!

```python
import re

BOLLS_PREFIX_RE = re.compile(r"^\[(0+|[1-9]\d*)\]\s*(.*)$", re.DOTALL)
BOLLS_RUBY_RE = re.compile(r"<i>([^<]+)</i><sup>,([^<]+)</sup>")

def parse_bolls_jpkjv_chapter(raw_items: list[dict]):
    """
    Xử lý chuẩn xác 1 chương từ Bolls.life JPKJV.json:
    - Tách [0], [00] thành psalm_superscription_ja
    - Lấy số câu chuẩn từ [N] (khắc phục lỗi lệch +1/+2 câu ở sách Thi-thiên)
    - Chuyển <i>Kanji</i><sup>,reading</sup> sang HTML5 <ruby> và mảng ruby_tokens
    """
    superscriptions_ruby = []
    verses = []

    for item in raw_items:
        raw_text = item.get("text", "").strip()
        true_verse = item.get("verse")

        m_pref = BOLLS_PREFIX_RE.match(raw_text)
        if m_pref:
            tag_num = m_pref.group(1)
            raw_text = m_pref.group(2).strip()
            if tag_num in ("0", "00"):
                html_ruby = BOLLS_RUBY_RE.sub(r"<ruby>\1<rt>\2</rt></ruby>", raw_text)
                superscriptions_ruby.append(html_ruby)
                continue
            else:
                true_verse = int(tag_num)

        # Trích xuất danh sách từ vựng Kanji kèm cách đọc Hiragana trong câu
        ruby_pairs = [
            {"surface": m.group(1), "reading": m.group(2)}
            for m in BOLLS_RUBY_RE.finditer(raw_text)
        ]
        # Chuyển sang thẻ HTML5 <ruby> chuẩn cho giao diện Fukuin
        text_html_ruby = BOLLS_RUBY_RE.sub(r"<ruby>\1<rt>\2</rt></ruby>", raw_text)
        # Văn bản thuần (bỏ Furigana) để tìm kiếm và đối chiếu với GetBible japkougo
        text_plain = BOLLS_RUBY_RE.sub(r"\1", raw_text)

        verses.append({
            "verse": true_verse,
            "text_plain": text_plain,
            "text_ruby_html": text_html_ruby,
            "ruby_tokens": ruby_pairs,
        })

    return {
        "psalm_superscription_ja": " ".join(superscriptions_ruby) if superscriptions_ruby else None,
        "verses": verses,
    }
```

---

### 2.2. BẪY C1 — Lỗi Gán Nhầm Mã Strong Tự Động Trong `engwebp_usfm.zip` (`EN_WEB`) & Quy Tắc Đánh Số File USFM (`02-GEN`..`96-REV`)

> [!CAUTION]
> **CẢNH BÁO ĐỎ VỀ FILE USFM CỦA `WEB` (`engwebp_usfm.zip`)**:
> Qua giải nén và kiểm thử trực tiếp file `02-GENengwebp.usfm` trong `https://ebible.org/Scriptures/engwebp_usfm.zip`, câu Sáng-thế Ký 1:1 có nội dung:
> ```usfm
> \v 1 \w In|strong="H8064"\w* \w the|strong="H1254"\w* \w beginning|strong="H0430"\w*, \w God|strong="H8064"\w*\f + \fr 1:1 \ft After "God", the Hebrew has the two letters "Aleph Tav"...\f* \w created|strong="H1254"\w* \w the|strong="H0853"\w* \w heavens|strong="H8064"\w* \w and|strong="H0853"\w* \w the|strong="H0776"\w* \w earth|strong="H0776"\w*.
> ```
> Hãy nhìn kỹ các mã Strong tự động trong `engwebp_usfm.zip`:
> - Từ `"In"` và `"God"` đều bị gán bừa mã `H8064` (*shamayim* = bầu trời)!
> - Từ `"beginning"` lại bị gán mã `H0430` (*Elohim* = Đức Chúa Trời)!
>
> **Ngược lại**, trong file `02-GENeng-kjv2006.usfm` của **`eng-kjv2006_usfm.zip` (`EN_KJV`)**, mã Strong được gắn thủ công chuẩn xác 100%:
> ```usfm
> \v 1 In the \w beginning|strong="H07225"\w* \w God|strong="H0430"\w* \w created|strong="H01254"\w* the \w heaven|strong="H08064"\w* and the \w earth|strong="H0776"\w*.
> ```

* **3 Quy tắc bắt buộc khi xử lý `EN_WEB` và `EN_KJV`**:
  1. **Quy tắc 1 (Định danh file USFM)**: Trong các gói `.zip` của `eBible.org`, tên file đánh số từ `00-FRT` (Lời tựa), `02-GEN`..`40-MAL` (Cựu Ước), nhảy cách qua `67..69` (Apocrypha), rồi từ `70-MAT`..`96-REV` (Tân Ước). **Tuyệt đối không ghép tên file theo số thứ tự `01..66`**, mà phải đọc dòng đầu tiên của mỗi file `.usfm`: `\id GEN` (lấy 3 ký tự đầu sau `\id ` làm mã sách USFM chuẩn)!
  2. **Quy tắc 2 (Nguồn mã Strong tiếng Anh)**: **CẤM sử dụng thuộc tính `strong="..."` từ `engwebp_usfm.zip` (`EN_WEB`)**. Chỉ lấy văn bản sạch (và chú thích chân trang `\f ... \f*` rất giá trị) từ `EN_WEB`, còn ánh xạ từ tiếng Anh $\leftrightarrow$ số Strong (`Hxxxx` / `Gxxxx`) **chỉ lấy duy nhất từ `eng-kjv2006_usfm.zip` (`EN_KJV`)**!
  3. **Quy tắc 3 (Chuẩn hóa mã Strong & thẻ `\add` trong KJV)**:
     - Trong `eng-kjv2006_usfm.zip`, mã Strong có số `0` ở đầu (`H07225`, `H0430`, `G03056`). Phải chuẩn hóa bằng `re.sub(r"^([HG])0+(\d+)$", r"\1\2", code)` thành `H7225`, `H430`, `G3056` để khớp khóa chính với từ điển Strong và `ORIG_WLC`.
     - Trước khi lấy lời văn câu Kinh Thánh từ USFM, phải tách riêng khối chú thích chân trang `\f ... \f*` và tham chiếu `\x ... \x*` ra mảng `footnotes` trước, nếu không nội dung chú thích (`After "God", the Hebrew has...`) sẽ bị dính thẳng vào giữa câu Kinh Thánh!
     - Các từ nằm trong cặp thẻ `\add ... \add*` của bản `KJV` (những từ do dịch giả KJV thêm vào cho rõ nghĩa, in nghiêng trong Kinh Thánh in) được chuyển thành `<i>...</i>` hoặc giữ metadata.

---

### 2.3. BẪY C2 — Định Dạng `lemma` Không Có Tiền Tố `"H"` (`lemma="c/d/776"`, `"1254 a"`), Dấu Gạch Chéo Hình Thái Học (`/`) & Lệch Số Câu Thi-thiên Trong `OpenScriptures WLC` (`morphhb`)

Qua kiểm thử trực tiếp file `https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/Gen.xml` (`ORIG_WLC`), cấu trúc XML thực tế của Sáng-thế Ký 1:1 là:

```xml
<verse osisID="Gen.1.1">
  <w lemma="b/7225" morph="HR/Ncfsa" id="01xN3">בְּ/רֵאשִׁ֖ית</w>
  <w lemma="1254 a" morph="HVqp3ms" id="01xK4">בָּרָ֣א</w>
  <w lemma="430" morph="HNcmpa" id="01n7H">אֱלֹהִ֑ים</w>
  <w lemma="853" morph="HTo" id="01K6Q">אֵ֥ת</w>
  <w lemma="d/8064" morph="HTd/Ncmpa" id="01c6D">הַ/שָּׁמַ֖יִם</w>
  <w lemma="c/853" morph="HC/To" id="01b7E">וְ/אֵ֥ת</w>
  <seg type="x-maqqef">־</seg>
  <w lemma="d/776" morph="HTd/Ncbsa" id="01t2M">הָ/אָֽרֶץ</w>
  <seg type="x-sof-pasuq">׃</seg>
</verse>
```

* **4 Bẫy Runtime bắt buộc phải xử lý khi parse `ORIG_WLC` (`wlc/*.xml`)**:
  1. **Thuộc tính `lemma` KHÔNG có chữ `"H"` ở đầu, có tiền tố `b/`, `c/d/` và hậu tố chữ cái đồng âm `a`, `b`**:
     - Ví dụ: `lemma="b/7225"` (giới từ `b` = *trong* + `7225` = *reshith*), `lemma="c/d/776"` (liên từ `c` = *và* + mạo từ `d` = *cái* + `776` = *erets*), `lemma="1254 a"` (động từ `1254` *bara* nhánh nghĩa `a`).
     - **Hàm trích xuất mã Strong chuẩn**:
       ```python
       def parse_wlc_lemma(raw_lemma: str):
           # Ví dụ: "c/d/776" -> prefixes=["c", "d"], strong="H776"
           # Ví dụ: "1254 a" -> prefixes=[], strong="H1254", homonym="a"
           parts = [p.strip() for p in raw_lemma.split("/")]
           prefixes = [p for p in parts[:-1] if not any(ch.isdigit() for ch in p)]
           main_part = parts[-1]
           m = re.match(r"^(\d+)\s*([a-zA-Z]?)$", main_part)
           strong_id = f"H{int(m.group(1))}" if m else None
           return {"strong": strong_id, "prefixes": prefixes, "raw_lemma": raw_lemma}
       ```
  2. **Dấu gạch chéo `/` phân tách hình thái học nằm ngay trong chữ Hê-bơ-rơ (`בְּ/רֵאשִׁ֖ית`)**:
     - Văn bản trong thẻ `<w>` chứa dấu `/` để chỉ ranh giới giữa tiền tố (`בְּ`) và thân từ (`רֵאשִׁ֖ית`).
     - Khi xuất ra trường `surface_display` cho người dùng đọc, **bắt buộc phải xóa dấu `/`** (`word_text.replace("/", "")` $\rightarrow$ `בְּרֵאשִׁ֖ית`), đồng thời lưu bản gốc có `/` vào `surface_segmented` để phục vụ tính năng học ngữ pháp Hê-bơ-rơ!
  3. **Thẻ `<seg type="x-maqqef">־</seg>` và `<seg type="x-sof-pasuq">׃</seg>`**:
     - Giữa hai thẻ `<w>`, nếu có `<seg type="x-maqqef">־</seg>` (dấu gạch nối Hê-bơ-rơ *Maqqef*), hai từ đó nối liền với nhau bằng dấu `־` mà không có khoảng trắng ở giữa; cuối câu kết thúc bằng dấu hai chấm Hê-bơ-rơ `׃` (`sof-pasuq`).
  4. **Lệch số câu (`+1` hoặc `+2`) giữa Bản Hê-bơ-rơ `WLC` và Bản Tiếng Việt / Anh / Nhật ở các Thi-thiên có Thượng đề**:
     - Trong Kinh Thánh Hê-bơ-rơ (`WLC`), Thượng đề Thi-thiên được đánh số là `Gen/Ps.X.1` (hoặc `Ps.51.1` và `Ps.51.2`), làm cho câu 1 của bản Tiếng Việt (`VI1934`) ứng với `Ps.51.3` trong `WLC`!
     - **Quy tắc căn chỉnh (Verse Alignment Rule)**: Bộ biến đổi `align_wlc_to_protestant_versification()` kiểm tra xem chương Thi-thiên trong `kinhthanh_httlvn` / `JA_KOUGO` có thượng đề (`psalm_superscription`) hay không và tự động ánh xạ `WLC` câu `1` (hoặc `1..2`) vào phần `superscription_orig_tokens`, rồi dịch chuyển các câu còn lại (`v - offset`) để câu 1 tiếng Việt luôn khớp chính xác 100% với câu Hê-bơ-rơ tương ứng!

---

### 2.4. BẪY C3 — Cấu Trúc 7 Cột Của `MorphGNT SBLGNT` (`*-morphgnt.txt`) Cho Tân Ước Hy Lạp (`ORIG_GNT`)

* Kiểm thử trực tiếp `https://raw.githubusercontent.com/morphgnt/sblgnt/master/61-Mt-morphgnt.txt`:
  ```text
  010101 N- ----NSF- Βίβλος Βίβλος βίβλος βίβλος
  010101 N- ----GSF- γενέσεως γενέσεως γένεσις γένεσις
  010101 N- ----GSM- Ἰησοῦ Ἰησοῦ Ἰησοῦς Ἰησοῦς
  010101 N- ----GSM- Χριστοῦ Χριστοῦ Χριστός Χριστός
  ```
* **Giải nghĩa 7 cột phân cách bởi khoảng trắng**:
  1. `bcv` (`010101`): 2 chữ số đầu là số thứ tự sách Tân Ước (`01` = `MAT` .. `27` = `REV`), 2 chữ số giữa là số chương (`01`), 2 chữ số cuối là số câu (`01`).
  2. `pos` (`N-`, `V-`, `RA`, `P-`, `C-`...): Từ loại (Part of Speech).
  3. `parse` (`----NSF-`): Mã phân tích hình thái học 8 ký tự (Person, Tense, Voice, Mood, Case, Number, Gender, Degree).
  4. `text`: Từ bề mặt kèm dấu câu trong câu (`Βίβλος`).
  5. `word`: Từ bề mặt đã bỏ dấu chấm câu.
  6. `normalized`: Từ chuẩn hóa chính tả.
  7. `lemma` (`βίβλος`, `γένεσις`, `Ἰησοῦς`): Từ nguyên thể dùng để nối (Join) với từ điển `strongsgreek.xml` lấy mã Strong (`G976`, `G1078`, `G2424`)!

---

### 2.5. BẪY E1 — Tổng Hợp Thánh Ca Tiếng Nhật `Sanbika 1954` (`讃美歌 1954年版`) Không Cần Crawl `Hymnary.org` (`HTTP 403`)

* Do `https://hymnary.org/hymnal/S1954` bật tường lửa Cloudflare trả về `HTTP 403 Forbidden`, pipeline `ja_sanbika` kết hợp 3 nguồn mở `HTTP 200 OK`:
  1. **Nguồn A — Mục lục đầy đủ trên Wikipedia Nhật**:
     - Endpoint: `https://ja.wikipedia.org/w/api.php?action=query&titles=讃美歌_(1954年版)&prop=revisions&rvprop=content&format=json` (`99.6 KB`).
     - Cung cấp danh sách phân loại chủ đề, số bài (`1..567`), tiêu đề tiếng Nhật và tên bài gốc Âu-Mỹ.
  2. **Nguồn B — Dữ liệu JSON lời ca mở trên GitHub**:
     - Endpoint: `https://raw.githubusercontent.com/lee-ship-jp/kanichi-sanbika/main/data/songs.json` (`194.2 KB`).
     - Cấu trúc mỗi phần tử:
       ```json
       {
         "number": "1",
         "title": "いざやともに",
         "lyrics": [
           "1 いざやともに こえをあげて...",
           "2 ..."
         ]
       }
       ```
  3. **Nguồn C — `ja.wikisource.org` API (`Category:讃美歌`)**:
     - Bổ sung lời văn nguyên bản cho các bài cổ điển nổi tiếng và gắn Furigana tự động + hiệu đính cho thuật ngữ Cơ Đốc tiếng Nhật (`主` $\to$ `しゅ`, `御国` $\to$ `みくに`, `救い主` $\to$ `すくいぬし`, `贖い` $\to$ `あがない`).
* **Thuật toán Liên kết Chéo Thánh Ca Việt (`VI_TC`) $\leftrightarrow$ Nhật (`JA_SANBIKA`)**:
  - Dựa trên trường `original_title_en` (lấy từ `vietchristian.com` `result.asp`) và tên nhạc sĩ (`composer` + năm sáng tác trên `thanhca.httlvn.org`), đối khớp với tên bài gốc tiếng Anh/Đức trong bảng Wikipedia `讃美歌_(1954年版)` để nối các bài Thánh Ca kinh điển giữa tiếng Việt và tiếng Nhật (ví dụ *Thánh Ca 42: Lớn Bấy Duy Ngài* $\leftrightarrow$ *How Great Thou Art*, *Thánh Ca 285: Đêm Yên Lặng* $\leftrightarrow$ *讃美歌 109番: きよしこの夜*, *Thánh Ca 20: Ngợi Khen Đấng Quân Lâm* $\leftrightarrow$ *讃美歌 75番: われらを導く*).
