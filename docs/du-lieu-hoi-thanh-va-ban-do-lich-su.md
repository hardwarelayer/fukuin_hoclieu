# Đặc Tả Dữ Liệu Hội Thánh (VN & JP), Bản Đồ Lịch Sử & Chỉ Mục Tìm Kiếm Nhanh Buổi Nhóm (`fukuin_hoclieu`)

> Tài liệu này định nghĩa cấu trúc dữ liệu trong kho `fukuin_hoclieu/data/` cho 4 module mới bổ sung:
> 1. **Danh bạ & Tọa độ Bản đồ Hội Thánh tại Việt Nam (`churches_vn.json`) và Nhật Bản (`churches_jp.json`)**.
> 2. **Quy trình Ban Biên Tập chuẩn hóa thông tin Hội Thánh từ đóng góp của người dùng (`submissions/` $\rightarrow$ `data/churches/`)**.
> 3. **Dữ liệu Bản đồ Hành trình Truyền giáo trong Kinh Thánh & Lịch sử (`data/maps/`)** tương thích với engine `map-svg.js` & `map-tuong-tac.js` của `tamquocchi`.
> 4. **Bảng Ánh Xạ Lệnh Tìm Kiếm Nhanh Buổi Nhóm (`data/search/worship_aliases.json`)**.

---

## 1. Schema Dữ Liệu Hội Thánh (`data/churches/`)

Dữ liệu Hội Thánh được chia thành 2 tập tin chính (`churches_vn.json` và `churches_jp.json`) nhưng tuân thủ cùng một Schema chuẩn để dùng chung component bản đồ và trang giới thiệu:

```jsonc
{
  "church_uid": "church:jp:tokyo-vietnamese-evangelical",
  "country_code": "JP",                   // "VN" | "JP"
  "region_id": "kanto",                   // VN: "bac"|"trung"|"nam"; JP: "hokkaido"|"tohoku"|"kanto"|"chubu"|"kansai"|"chugoku"|"shikoku"|"kyushu"
  "province_code": "JP-13",               // Mã tỉnh/thành (VD: "VN-DN" Đà Nẵng, "VN-SG" TP.HCM, "JP-13" Tokyo, "JP-27" Osaka)
  "province_name": {
    "vi": "Tokyo",
    "ja": "東京都",
    "ja_reading": "とうきょうと",
    "han_viet": "ĐÔNG KINH ĐÔ"
  },
  "slug": "jp-tokyo-hoi-thanh-tin-lanh-nguoi-viet-tokyo",
  "name": {
    "vi": "Hội Thánh Tin Lành Người Việt tại Tokyo",
    "ja": "東京ベトナム人キリスト教会",
    "ja_reading": "とうきょうべとなむじんきりすときょうかい",
    "en": "Tokyo Vietnamese Evangelical Church"
  },
  "denomination_vi": "Liên hữu Tin Lành Việt Nam tại Nhật Bản",
  "languages": ["vi", "ja"],              // Ngôn ngữ nhóm lại ("vi", "ja", "en")
  "has_vietnamese_fellowship": true,      // Phục vụ bộ lọc nhanh cho người Việt tại Nhật
  "map_coord": {
    "map_id": "map_jp",                   // "map_vn" | "map_jp"
    "gx": 46,                             // Tọa độ ô lưới X trên bản đồ vẽ tay SVG (dùng cho ?x=46&y=38)
    "gy": 38,                             // Tọa độ ô lưới Y trên bản đồ vẽ tay SVG
    "lat": 35.7012,                       // Vĩ độ thực tế (để mở link Google Maps chỉ đường)
    "lng": 139.7003                       // Kinh độ thực tế
  },
  "address": {
    "vi": "Shinjuku-ku, Hyakunincho 1-xx-xx, Tokyo",
    "ja": "〒169-0073 東京都新宿区百人町1-xx-xx",
    "station_guide_vi": "Cách ga JR Shin-Okubo (新大久保駅) 4 phút đi bộ, hoặc ga Okubo (大久保駅) cửa Bắc 3 phút."
  },
  "worship_schedule": [
    {
      "day": "Chúa Nhật",
      "time": "14:00 - 16:00",
      "service_name_vi": "Thờ phượng Chính lễ (Tiếng Việt & Thông dịch Nhật)",
      "period_tag": "afternoon"           // "morning" | "afternoon" | "evening"
    },
    {
      "day": "Thứ Năm",
      "time": "20:00 - 21:30",
      "service_name_vi": "Học Kinh Thánh & Cầu nguyện (Online & Trực tiếp)",
      "period_tag": "evening"
    }
  ],
  "editorial_intro": {
    "founded_year": 2012,
    "summary_vi": "Điểm nhóm và thờ phượng ấm cúng dành cho du học sinh, kỹ sư, thực tập sinh và gia đình người Việt đang sinh sống tại vùng Kanto (Tokyo, Saitama, Chiba, Kanagawa).",
    "history_paragraphs_vi": [
      "Khởi đầu từ một nhóm nhỏ các du học sinh và tín hữu người Việt nhóm lại cầu nguyện tại Shinjuku vào năm 2012...",
      "Hiện nay Hội Thánh duy trì sinh hoạt đều đặn mỗi chiều Chúa Nhật với các ban Thanh niên, Gia đình trẻ và lớp hỗ trợ đời sống cho tân du học sinh."
    ],
    "key_verse_uid": "MAT.18.20",
    "favorite_hymn_uid": "tc:218",
    "illustration_asset_key": "church-sketch-jp-tokyo-v1"
  },
  "contact": {
    "website": "https://...",
    "facebook": "https://facebook.com/...",
    "phone_public": "+81-3-xxxx-xxxx"
  },
  "verification": {
    "status": "verified",                 // Chỉ những bản ghi "verified" mới được xuất bản lên fukuin
    "verified_by": "editorial_board",
    "last_updated": "2026-11-08",
    "contributor_note": "Cung cấp bởi Ban Điều Hành HT, Ban biên tập Fukuin xác minh."
  }
}
```

### Quy Trình Ban Biên Tập Xử Lý Đóng Góp Từ Người Dùng (`tools/ingest_church_submission.py`)
1. Người dùng gửi thông tin Hội Thánh qua form đóng góp trên web (tạo ra tệp JSON nháp trong `crawl_factory/church_submissions/pending/`).
2. Ban biên tập kiểm tra thông tin thực tế (địa chỉ, giờ nhóm, kênh liên hệ chính thức), bổ sung tọa độ lưới bản đồ `(gx, gy)`, gắn câu gốc/Thánh Ca liên kết và chuyển trạng thái `verification.status = "verified"`.
3. Chạy `python -X utf8 tools/validate_hoclieu.py`: cổng kiểm đảm bảo mọi `church_uid` là duy nhất, tọa độ `(gx, gy)` nằm đúng trên ô đất liền (`terrain != 'water'`) của bản đồ `map_vn` / `map_jp`, và mọi `key_verse_uid` / `favorite_hymn_uid` đều tồn tại.

---

## 2. Schema Bản Đồ Hành Trình Truyền Giáo Lịch Sử & Kinh Thánh (`data/maps/`)

Để tái sử dụng hoàn toàn bộ vẽ đường cong Bézier (`map-svg.js`) và bộ chạy thuyền/điểm động (`map-tuong-tac.js`) của `hoctamquoc`, dữ liệu bản đồ trong `fukuin_hoclieu/data/maps/` gồm 2 phần:

### 2.1. Lưới Địa Hình Nền (`data/maps/grids/{map_id}.json`)
Chúng ta định nghĩa 3 lưới bản đồ vẽ tay:
1. **`map_biblical_world.json`**: Vùng Địa Trung Hải, Ai Cập, Bán đảo Si-na-i, Ca-na-an / Y-sơ-ra-ên, Lưỡng Hà (Mesopotamia), Tiểu Á, Hy Lạp, Ý (Rô-ma).
2. **`map_vn.json`**: Lưới bản đồ Việt Nam + các tuyến truyền giáo lịch sử từ Đà Nẵng (1911) đi khắp 3 miền.
3. **`map_jp.json`**: Lưới bản đồ Nhật Bản + các trung tâm lịch sử Cơ Đốc & Hội Thánh hiện đại.

### 2.2. Kịch Bản Tuyến Hành Trình (`data/maps/journeys.json`)
```jsonc
{
  "journey_id": "paul_mission_2",
  "map_id": "map_biblical_world",
  "category": "biblical_nt",              // "biblical_ot" | "biblical_nt" | "history_vn" | "history_jp"
  "title": {
    "vi": "Hành Trình Truyền Giáo Lần Thứ Hai Của Sứ Đồ Phao-lô (49–52 SCN)",
    "en": "Paul's Second Missionary Journey",
    "ja": "パウロの第二次伝道旅行"
  },
  "scripture_range": "ACT.15.36-ACT.18.22",
  "segments": [
    {
      "segment_order": 1,
      "from_place_id": "place:antioch_syria",
      "to_place_id": "place:troas",
      "transport_mode": "land",           // "land" (.duong-bo) | "sea" (.duong-thuy -> có thuyền chạy trên map-tuong-tac.js!)
      "waypoints_grid": [[58, 28], [52, 24], [44, 21], [36, 18]],
      "scripture_ref": "ACT.16.1-8",
      "event_title_vi": "Khải tượng người Ma-xê-đoan tại Tơ-rô-ách",
      "event_summary_vi": "Tại Tơ-rô-ách, ban đêm Phao-lô thấy một người Ma-xê-đoan đứng cầu xin rằng: 'Hãy qua xứ Ma-xê-đoan cứu giúp chúng tôi!'",
      "story_slug": "nt_24_paul_macedonian_call"
    },
    {
      "segment_order": 2,
      "from_place_id": "place:troas",
      "to_place_id": "place:philippi",
      "transport_mode": "sea",            // Vẽ tuyến đường thủy qua biển Ê-giê kèm thuyền buồm
      "waypoints_grid": [[36, 18], [33, 15], [30, 13]],
      "scripture_ref": "ACT.16.11-15",
      "event_title_vi": "Vượt biển sang Âu Châu — Hội Thánh đầu tiên tại Phi-líp (Bà Ly-đi)",
      "event_summary_vi": "Lần đầu tiên Tin Lành vượt biển từ Á Châu sang Âu Châu..."
    }
  ]
}
```

---

## 3. Schema Chỉ Mục Tìm Kiếm Nhanh Buổi Nhóm (`data/search/worship_aliases.json`)

Để phục vụ thanh lệnh nhanh `worship-quick-jump.js` dưới `5ms` trên client mà không cần tải dữ liệu nặng, `build_hoclieu.py` sinh ra tệp chỉ mục siêu nhẹ `worship_aliases.json` (~18 KB sau khi nén gzip):

```jsonc
{
  "command_prefixes": {
    "hymn_vi": ["tc", "thanhca", "thanh ca", "thánh ca", "bai", "bài"],
    "hymn_ja": ["sb", "sanbika", "讃美歌", "さんびか"],
    "ktdd": ["ktdd", "ktđđ", "dd", "đđ", "doidap", "doi dap", "đối đáp"]
  },
  "books_lookup": [
    {
      "book_id": "PSA",
      "slug": "thi-thien",
      "chapters": 150,
      "name_vi": "Thi-thiên",
      "name_ja": "詩篇",
      "aliases": [
        "thi thien", "thi-thien", "thithien", "tt", "thi", "tv", "thanh vuong",
        "psa", "psalm", "psalms", "ps",
        "詩篇", "詩", "しへん"
      ]
    },
    {
      "book_id": "JHN",
      "slug": "giang",
      "chapters": 21,
      "name_vi": "Giăng",
      "name_ja": "ヨハネによる福音書",
      "aliases": [
        "giang", "giăng", "gi", "ga", "phuc am giang",
        "jhn", "john", "jn",
        "ヨハネ", "よはね", "約翰"
      ]
    }
  ],
  "hymns_quick_titles": {
    "1": ["Cúi Xin Vua Thánh Ngự Lai", "1-cui-xin-vua-thanh-ngu-lai", 67],
    "19": ["Thánh! Thánh! Thánh!", "19-thanh-thanh-thanh", 66],
    "42": ["Lớn Bấy Duy Ngài", "42-lon-bay-duy-ngai", null]
  },
  "ktdd_quick_titles": {
    "1": ["Đấng Tạo Hóa", "1-dang-tao-hoa", "Sáng-thế ký 1:1-6"],
    "15": ["Đấng Chăn Chiên Hiền Lành", "15-dang-chan-chien-hien-lanh", "Thi-thiên 23"]
  }
}
```
* Chỉ với 1 tệp `worship_aliases.json` (18 KB) này được nạp sẵn trong bộ nhớ trình duyệt:
  - Gõ `tt 90` $\rightarrow$ khớp `aliases: "tt"` (`PSA`) + chương `90` ($\le 150$) $\rightarrow$ nhảy ngay tới `/kinh-thanh/thi-thien/90`.
  - Gõ `tc 19` $\rightarrow$ khớp `command_prefixes.hymn_vi` + số `19` $\rightarrow$ hiện ngay tiêu đề *"Thánh Ca 19: Thánh! Thánh! Thánh! (讃美歌 66)"* và nhảy tới `/thanh-ca/19-thanh-thanh-thanh`.
  - Gõ `ktdd 15` $\rightarrow$ khớp `command_prefixes.ktdd` + số `15` $\rightarrow$ hiện ngay *"KTĐĐ 15: Đấng Chăn Chiên Hiền Lành (Thi-thiên 23)"* và nhảy tới `/kinh-thanh-doi-dap/15-dang-chan-chien-hien-lanh`.

