# Đặc Tả Kiến Trúc Học Liệu & Schema Dữ Liệu (`fukuin_hoclieu/data/`)

> Tài liệu này quy định cấu trúc tệp JSON chuẩn hóa trong thư mục `fukuin_hoclieu/data/` và các cổng kiểm toàn vẹn tự động (`validate_hoclieu.py`). Mọi công cụ trong `fukuin_hoclieu/tools/` và `fukuin/tools/prepare_site.py` đều phải tuân thủ hợp đồng Schema này.

---

## 1. Cấu Trúc Tổ Chức Các Tệp Trong `data/`

```text
fukuin_hoclieu/data/
├── manifest.json                       # Thông tin phiên bản, tổng số bản ghi, checksum
├── bible/
│   ├── books.json                      # Danh mục 66 sách (USFM id, tên Việt/Anh/Nhật/Hê-bơ-rơ/Hy Lạp, số chương)
│   ├── archaic_glossary.json           # Từ điển giải nghĩa từ cổ & tên riêng phiên âm trong bản 1925
│   ├── cross_references.json           # Đồ thị tham chiếu chéo 2 chiều giữa các câu (⚓)
│   ├── famous_passages.json            # Danh mục 120+ Đoạn Kinh Thánh Nổi Tiếng (tách riêng làm trang SEO chủ lực)
│   └── chapters/
│       ├── GEN.json                    # Toàn bộ 50 chương Sáng-thế Ký (VI1934 + WEB + KJV + JA Kougo/Bungo + WLC/GNT)
│       ├── EXO.json                    # Toàn bộ 40 chương Xuất Ê-díp-tô Ký
│       └── ... (66 tệp theo mã USFM)
├── lexicon/
│   ├── strongs_hebrew.json             # Từ điển gốc Hê-bơ-rơ Strong (H1..H8674) kèm nghĩa Việt - Anh - Nhật
│   ├── strongs_greek.json              # Từ điển gốc Hy Lạp Strong (G1..G5624) kèm nghĩa Việt - Anh - Nhật
│   └── lumilearn_bridge.json           # Bảng ánh xạ từ vựng Kinh Thánh/Thánh Ca sang khóa lex_jp_* / lex_en_* của LumiLearnWeb
├── stories/
│   ├── stories_index.json              # Mục lục 60 Câu chuyện Kinh Thánh theo 8 Kỷ nguyên
│   ├── biblical_cast.json              # Hồ sơ tạo hình nhân vật & bối cảnh thống nhất cho tranh vẽ bút chì
│   └── items/
│       └── {story_slug}.json           # Nội dung câu chuyện đa ngữ + tọa độ câu gốc + manifest tranh bút chì
├── hymns/
│   ├── categories.json                 # 18 chủ đề lớn (cat_top) & danh sách chủ đề con (cat_sub)
│   ├── hymns_index.json                # Mục lục nhẹ 903 bài + liên kết Sanbika 1954 (Nhật) & Hymn tiếng Anh
│   └── items/
│       └── hymns_all.json              # Chi tiết 903 bài Thánh Ca Việt + lời Anh gốc + lời Nhật Sanbika 1954 (kèm Furigana)
├── ktdd/
│   └── responsive_readings.json        # Toàn bộ 100 bài Kinh Thánh Đối Đáp + liên kết câu gốc
├── quotes/
│   ├── topics_moods.json               # Các chủ đề trích dẫn SEO & tâm trạng Dưỡng Linh ("Khi lo lắng", "Bình an"...)
│   └── daily_quotes_366.json           # 366 câu gốc hằng ngày (01-01 đến 12-31)
├── history/
│   └── on_this_day_366.json            # Ngày này năm xưa (Sự kiện lịch sử Hội Thánh, Thánh Ca & Tin Lành VN)
├── plans/
│   └── reading_plans.json              # 4 lộ trình đọc Kinh Thánh nguyên năm (365 ngày)
├── quizzes/
│   ├── quiz_by_book.json               # Ngân hàng câu hỏi trắc nghiệm theo từng sách/chương (3 cấp độ)
│   └── memory_verses_drills.json       # Bài tập thuộc câu gốc (điền từ khuyết, sắp xếp mệnh đề)
└── entities/
    ├── characters.json                 # Nhân vật Kinh Thánh tiêu biểu & danh sách câu xuất hiện
    └── locations.json                  # Địa danh Kinh Thánh (kèm tọa độ bản đồ cổ đại) & câu xuất hiện
```

> **Chi tiết Schema cho Danh bạ Hội Thánh (`data/churches/`), Bản đồ Hành trình Truyền giáo (`data/maps/`) và Chỉ mục Tìm kiếm Nhanh Buổi Nhóm (`data/search/worship_aliases.json`)**: Xem tại [du-lieu-hoi-thanh-va-ban-do-lich-su.md](./du-lieu-hoi-thanh-va-ban-do-lich-su.md).

---

## 2. Đặc Tả Schema Chi Tiết Từng Thực Thể

### 2.1. Danh Mục Sách Kinh Thánh (`data/bible/books.json`)
```jsonc
{
  "book_id": "GEN",                     // Khóa chuẩn USFM 3 chữ cái
  "book_order": 1,                      // Thứ tự 1..66 (1..39: OT, 40..66: NT)
  "testament": "OT",                    // "OT" (Cựu Ước) | "NT" (Tân Ước)
  "division": "pentateuch",             // Ngũ Kinh | Lịch Sử | Thơ Ca | Đại Tiên Tri | Tiểu Tiên Tri | Phúc Âm | Công Vụ | Thư Tín | Tiên Tri
  "httlvn_code": "sa",                  // Mã trên kinhthanh.httlvn.org
  "tinlanh_slug": "sangtheky",          // Mã trên www.tinlanh.com
  "slug": "sang-the-ky",                // Slug URL chuẩn trên fukuin
  "name_vi": "Sáng-thế Ký",             // Tên chuẩn Bản Truyền Thống 1925
  "name_vi_modern": "Sáng Thế Ký",      // Tên gọi phổ thông không gạch nối (hỗ trợ tìm kiếm)
  "name_en": "Genesis",
  "abbr_vi": "Sáng",
  "chapter_count": 50,
  "verse_count": 1533,
  "summary_vi": "Khởi nguyên của vũ trụ, loài người, sự sa ngã và giao ước của Đức Chúa Trời với Áp-ra-ham, Y-sác, Gia-cốp, Giô-sép.",
  "key_verses": ["GEN.1.1", "GEN.1.27", "GEN.12.2-3", "GEN.50.20"]
}
```

### 2.2. Chương & Câu Kinh Thánh (`data/bible/chapters/{BOOK_ID}.json`)
```jsonc
{
  "chapter_uid": "GEN.1",
  "book_id": "GEN",
  "chapter_number": 1,
  "audio_meta": {
    "httlvn_path": "/Audio/VI1934/1-ms-nguyen-thi/sa/1.mp3"
  },
  "sections": [
    {
      "major_title": "Về thời cổ, từ buổi sáng thế đến đời Áp-ra-ham",
      "major_range": "Từ đoạn 1 đến 11:9",
      "sub_title": "Tạo thành trời đất",
      "start_verse": 1,
      "end_verse": 31
    }
  ],
  "verses": [
    {
      "verse_uid": "GEN.1.1",
      "verse_number": 1,
      "is_paragraph_start": true,
      "is_paragraph_end": true,
      "text_vi1925": "Ban đầu Đức Chúa Trời dựng nên trời đất.",
      "text_en_web": "In the beginning, God created the heavens and the earth.",
      "text_en_kjv": "In the beginning God created the heaven and the earth.",
      "text_ja_kougo": "はじめに神は天と地とを創造された。",
      "text_ja_bungo": "元始に神天地を創造たまへり。",
      "orig_lang": "he",
      "orig_text": "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ",
      "orig_tokens": [
        { "surface": "בְּרֵאשִׁית", "strongs": "H7225", "translit": "bə·rê·šîṯ", "gloss_vi": "Ban đầu", "gloss_en": "In the beginning" },
        { "surface": "בָּרָא", "strongs": "H1254", "translit": "bā·rā", "gloss_vi": "dựng nên", "gloss_en": "created" },
        { "surface": "אֱלֹהִים", "strongs": "H430", "translit": "’ĕ·lō·hîm", "gloss_vi": "Đức Chúa Trời", "gloss_en": "God" }
      ],
      "ja_tokens": [
        { "t": "はじめ", "r": "はじめ", "dict": "lex_jp_hajime" },
        { "t": "に", "p": true },
        { "t": "神", "r": "かみ", "hv": "THẦN", "dict": "lex_jp_kami", "strongs_ref": "H430" },
        { "t": "は", "p": true },
        { "t": "天", "r": "てん", "hv": "THIÊN", "dict": "lex_jp_ten" },
        { "t": "と", "p": true },
        { "t": "地", "r": "ち", "hv": "ĐỊA", "dict": "lex_jp_chi" },
        { "t": "とを", "p": true },
        { "t": "創造", "r": "そうぞう", "hv": "SÁNG TẠO", "dict": "lex_jp_souzou", "strongs_ref": "H1254" },
        { "t": "された。", "p": true }
      ],
      "cross_references": ["JHN.1.1-2", "HEB.11.3", "PSA.33.6"],
      "famous_passage_id": "passage:sang-tao-troi-dat",
      "story_ids": ["ot_01_creation"],
      "topics": ["sang-tao", "duc-chua-troi"],
      "ktdd_ids": ["ktdd:001"],
      "hymn_ids": ["tc:023"],
      "entities": [],
      "archaic_terms": [
        { "term": "dựng nên", "modern_vi": "sáng tạo / tạo dựng", "han_viet": "SÁNG TẠO (創造)", "strongs": "H1254" }
      ]
    }
  ]
}
```

### 2.3. Thánh Ca (`data/hymns/items/hymns_all.json`)
```jsonc
{
  "hymn_uid": "tc:001",
  "number": 1,
  "slug": "cui-xin-vua-thanh-ngu-lai",
  "title_vi": "Cúi Xin Vua Thánh Ngự Lai",
  "title_en": "Come, Thou Almighty King",
  "sanbika_1954": {
    "number": 67,
    "title_ja": "全能の父なる神よ",
    "title_ruby": "ぜんのうのちちなるかみよ",
    "tune_name": "ITALIAN HYMN (MOSCOW)"
  },
  "category_top": "THỜ PHƯỢNG",
  "category_sub": "Ngợi khen Đức Chúa Trời",
  "composer": "Felice de Giardini",
  "composed_year": 1769,
  "lyricist": "Charles Wesley",
  "lyrics_year": 1757,
  "is_public_domain": true,
  "rhythm_hint": "B1L",                 // Ký hiệu điệu/nhịp từ bản hợp âm
  "default_key": "G",                   // Giọng chuẩn (phục vụ nút Transpose hợp âm)
  "stanzas": [
    {
      "stanza_number": 1,
      "type": "verse",                  // "verse" | "chorus"
      "lines_plain": [
        "Cúi xin Vua Thánh ngự lai,",
        "Hộ tôi cung chúc danh Ngài; Hát lên khen ngợi;",
        "Ngợi Cha sáng láng trên trời, Là danh chiến thắng muôn đời,",
        "Nguyện quang lâm trên chính tôi, Chúa thánh muôn đời."
      ],
      "lines_chordpro": [
        "[G]1.Cúi xin Vua [C]Thánh [D7]ngự [G]lai,",
        "Hộ tôi cung [Am]chúc danh [D7]Ngài; [G]Hát lên khen [Bm]ngợi;",
        "[D7]Ngợi Cha sáng [G]láng trên trời, [D7]Là danh chiến [G]thắng muôn đời,",
        "[Em]Nguyện quang lâm [Bm]trên chính tôi, [C]Chúa thánh [D7]muôn [G]đời."
      ]
    }
  ],
  "related_verses": ["PSA.95.1-3", "REV.19.16"],
  "media_refs": {
    "has_musicxml": true,
    "sheet_endpoint": "/Download/SheetMusic/1",
    "audio_url": "https://audio.httlvn.org/TC/thanh-ca/mp3/1.mp3",
    "youtube_beat_id": "ukgE...",
    "youtube_karaoke_id": "W..."
  }
}
```

### 2.4. Kinh Thánh Đối Đáp (`data/ktdd/responsive_readings.json`)
```jsonc
{
  "ktdd_uid": "ktdd:001",
  "number": 1,
  "slug": "dang-tao-hoa",
  "title_vi": "Đấng Tạo Hóa",
  "source_passages": [
    {
      "label": "Sáng-thế ký 1:1-6",
      "book_id": "GEN",
      "chapter": 1,
      "verse_start": 1,
      "verse_end": 6,
      "turns": [
        { "role": "leader", "text": "Ban đầu Đức Chúa Trời dựng nên trời đất.", "verse_uid": "GEN.1.1" },
        { "role": "congregation", "text": "Vả, đất là vô hình và trống không, sự mờ tối ở trên mặt vực; Thần Đức Chúa Trời vận hành trên mặt nước.", "verse_uid": "GEN.1.2" }
      ]
    }
  ],
  "related_hymns": ["tc:001", "tc:023"]
}
```

### 2.5. Ngày Này Năm Xưa (`data/history/on_this_day_366.json`)
```jsonc
{
  "day_key": "10-31",                   // MM-DD (366 ngày, kể cả 02-29)
  "events": [
    {
      "event_uid": "hist:10-31:1517",
      "year": 1517,
      "category": "church_history",     // "church_history" | "vietnam_mission" | "hymn_story" | "bible_translation"
      "title_vi": "Martin Luther đóng 95 Luận đề tại Wittenberg — Khởi đầu cuộc Cải Chánh Giáo Hội",
      "summary_vi": "Ngày 31/10/1517, Martin Luther niêm yết 95 Luận đề trước cửa nhà thờ lâu đài Wittenberg, khẳng định chân lý Kinh Thánh Duy Nhất (Sola Scriptura) và Đức Tin Duy Nhất (Sola Fide).",
      "related_verses": ["ROM.1.17", "EPH.2.8-9"],
      "related_hymns": ["tc:044"]       // Thánh Ca 44: Lâu Đài Bền Vững (A Mighty Fortress Is Our God - Martin Luther)
    }
  ]
}
```

---

## 3. Các Cổng Kiểm Tự Động (`tools/validate_hoclieu.py`)

Trước khi dữ liệu được phép chuyển sang `fukuin`, lệnh `python -X utf8 tools/validate_hoclieu.py` phải kiểm tra và đạt `PASSED` cho 6 bất biến sau:

1. **Bất biến Số lượng Kinh Thánh (`Bible Completeness Gate`)**:
   - Đủ 66 sách (`39` Cựu Ước + `27` Tân Ước), đúng `1.189` chương, không có câu nào rỗng (`text_vi1925 == ""`) hoặc còn sót thẻ HTML/ký tự `⚓` chưa tách.
2. **Bất biến Đối chiếu 2 nguồn (`Dual-Source Diff Gate`)**:
   - Mọi khác biệt giữa `kinhthanh_httlvn` và `tinlanh_com` phải được ghi nhận và giải quyết trong bảng `known_errata_resolutions.json`.
3. **Bất biến Toàn vẹn Đồ thị 2 chiều (`Bidirectional Graph Gate`)**:
   - Nếu `GEN.1.1` trỏ tới `ktdd:001` và `tc:023`, thì bản ghi `ktdd:001` và `tc:023` bắt buộc phải tồn tại và trỏ ngược về `GEN.1.1`.
   - Mọi mã `verse_uid` trong `cross_references`, `topics_moods`, `daily_quotes_366`, `reading_plans`, `quiz_by_book` đều phải tồn tại trong `data/bible/chapters/`.
4. **Bất biến Cú pháp Hợp âm (`ChordPro Syntax Gate`)**:
   - Mọi cặp ngoặc vuông `[...]` trong `lines_chordpro` của 903 bài Thánh Ca phải đóng mở cân bằng và là ký hiệu hợp âm hợp lệ (`^[A-G][#b]?(m|maj|min|dim|aug|sus|add|\d)*(\/[A-G][#b]?)?$`).
5. **Bất biến Phủ kín 366 Ngày (`Calendar Coverage Gate`)**:
   - `daily_quotes_366.json` và `on_this_day_366.json` phải phủ đủ 366 khóa `MM-DD` (bao gồm `02-29`).
   - Mỗi lộ trình trong `reading_plans.json` phải phủ đủ 365 ngày (`day: 1..365`).
6. **Bất biến Sạch Bản quyền (`Copyright Sanitization Gate`)**:
   - Quét toàn bộ `data/` đảm bảo không chứa văn bản của các bản dịch thương mại (`RVV11`, `BD2011`, `NVB`, `BPT`) và không chứa dấu vết URL nội bộ của công cụ crawl thô.

