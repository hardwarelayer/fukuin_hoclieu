# Kiến trúc Tuyển tập Câu chuyện Kinh Thánh & Pipeline Minh họa Bút chì (Pencil Sketch Illustrations)

Tài liệu này định nghĩa kiến trúc nội dung và quy trình sản xuất hình ảnh minh họa cho chuyên mục **Câu chuyện Kinh Thánh (`stories/`)** trong `fukuin_hoclieu` và `fukuin`, kế thừa mô hình **30 bài học tự sự** của `hoctamquoc` và **Shared Media Pipeline (Content-Addressed Visual Cast)** của `LumiLearnWeb_hoclieu`.

---

## 1. Triết lý & Định vị Độc bản

Thay vì chỉ hiển thị các chương Kinh Thánh dạng văn bản thuần túy, `fukuin` xây dựng một **Tuyển tập Câu chuyện Kinh Thánh kinh điển** (từ *Sáng tạo Thế giới*, *Con tàu Nô-ê*, *Áp-ra-ham*, *Môi-se qua Biển Đỏ*, * Đa-vít & Gô-li-át* đến *Chúa Giê-xu Giáng sinh*, *Bài giảng trên Núi*, *Người Sa-ma-ri nhân lành*, *Sự Phục sinh*...):

1. **Phong cách Nghệ thuật Bút chì Cổ điển (Classical Graphite & Charcoal Pencil Sketch)**:
   - Lấy cảm hứng từ tranh khắc và phác thảo chì cổ điển châu Âu thế kỷ 19 (Gustave Doré, Rembrandt sketches) trên nền giấy da ấm (`#FAF7F0`).
   - Mang lại cảm giác trang nghiêm, vượt thời gian, nghệ thuật cao, nhẹ dung lượng (tối ưu tuyệt đối cho WebP/AVIF và chế độ đọc ban đêm/người cao tuổi), đồng thời tạo bản sắc thị giác hoàn toàn khác biệt với các trang Kinh Thánh thông thường.
2. **Kết nối Trực tiếp với Văn bản Gốc 6 Phiên bản**:
   - Mỗi phân cảnh (Scene) trong câu chuyện đều gắn chặt với tọa độ câu Kinh Thánh (`canonical_ref`, ví dụ `GEN.6.9-22`). Người đọc có thể vừa xem tranh chì, vừa đọc lời dẫn chuyện dễ hiểu, vừa bấm mở đối chiếu câu Kinh Thánh gốc bằng tiếng Việt (`VI1934`), tiếng Anh (`WEB`/`KJV`), tiếng Nhật (`Kougo`/`Bungo`) và từ gốc Hê-bơ-rơ/Hy Lạp.

---

## 2. Cấu trúc Học liệu Câu chuyện Kinh Thánh (`data/stories/`)

Dự kiến giai đoạn 1 gồm **60 câu chuyện cốt lõi** (30 câu chuyện Cựu Ước + 30 câu chuyện Tân Ước), chia thành 8 Kỷ nguyên (Eras):

| Kỷ nguyên (`era_id`) | Tên Kỷ nguyên | Số bài | Các câu chuyện tiêu biểu |
| :--- | :--- | :---: | :--- |
| `era_01_creation_patriarchs` | Sáng Thế & Các Tổ Phụ | 10 | Sáng tạo muôn vật (`GEN.1-2`), Vườn Ê-đen, Tàu Nô-ê (`GEN.6-9`), Tháp Ba-bên, Tiếng gọi Áp-ra-ham (`GEN.12`), Giấc mơ Gia-cốp, Giô-sép tại Ai Cập (`GEN.37-45`) |
| `era_02_exodus_conquest` | Xuất Ê-díp-tô & Đất Hứa | 8 | Môi-se trong giỏ cói, Bụi gai cháy (`EXO.3`), Vượt qua Biển Đỏ (`EXO.14`), Mười Điều Răn (`EXO.20`), Thành Giê-ri-cô (`JOS.6`) |
| `era_03_judges_kings` | Các Quan Xét & Vương Quốc | 7 | Gê-đê-ôn, Ru-tơ (`RUT.1-4`), Đa-vít và Gô-li-át (`1SA.17`), Sự khôn ngoan của Sa-lô-môn (`1KI.3`) |
| `era_04_prophets_exile` | Các Tiên Tri & Lưu Đày | 5 | Ê-li trên núi Cạt-mên (`1KI.18`), Giô-na và cá lớn (`JON.1-4`), Đa-ni-ên trong hang sư tử (`DAN.6`), Hoàng hậu Ê-xơ-tê (`EST.4`) |
| `era_05_gospel_nativity_ministry` | Chúa Giê-xu Giáng Sinh & Thi Hành Chức Vụ | 10 | Thiên sứ báo tin & Giáng sinh tại Bết-lê-hem (`LUK.2`), Phép báp-têm tại sông Giô-đanh, Bài giảng trên Núi (`MAT.5-7`), Dẹp yên sóng gió |
| `era_06_parables_miracles` | Các Ẩn Dụ & Phép Lạ | 8 | Người Sa-ma-ri nhân lành (`LUK.10`), Đứa con hoang đàng (`LUK.15`), Người gieo giống, Hóa bánh cho 5.000 người, La-xa-rơ sống lại (`JOH.11`) |
| `era_07_passion_resurrection` | Thương Khó & Phục Sinh | 6 | Vào thành Giê-ru-sa-lem, Tiệc Thánh cuối cùng, Vườn Ghết-sê-ma-nê, Thập tự giá và Sự Phục Sinh (`LUK.22-24`), Đường đi Ê-ma-út |
| `era_08_early_church` | Hội Thánh Đầu Tiên | 6 | Lễ Ngũ Tuần (`ACT.2`), Phao-lô trên đường Đa-mách (`ACT.9`), Hành trình truyền giáo, Khải huyền về Trời Mới Đất Mới (`REV.21`) |

---

## 3. Schema Dữ liệu Câu chuyện (`data/stories/{story_slug}.json`)

```json
{
  "story_id": "ot_03_noah_ark",
  "order_index": 3,
  "era_id": "era_01_creation_patriarchs",
  "slug_vi": "con-tau-no-e-va-cau-vong-giao-uoc",
  "title": {
    "vi": "Con Tàu Nô-ê và Cầu Vồng Giao Ước",
    "en": "Noah's Ark and the Rainbow Covenant",
    "ja": "ノアの箱舟と契約の虹",
    "ja_ruby": "ノアのはこぶねとけいやくのにじ"
  },
  "primary_scripture_range": "GEN.6.9-GEN.9.17",
  "key_verse_id": "GEN.9.13",
  "characters": ["char_noah"],
  "locations": ["loc_ararat"],
  "hero_illustration": {
    "asset_key": "biblical-story-ot-03-noah-ark-hero-v1",
    "alt_vi": "Tranh vẽ chì cảnh con tàu Nô-ê bằng gỗ gô-phe giữa cơn đại hồng thủy và chim bồ câu ngậm nhành ô-li-ve",
    "caption_vi": "Chim bồ câu trở về mang theo một lá ô-li-ve tươi (Sáng-thế Ký 8:11)"
  },
  "scenes": [
    {
      "scene_index": 1,
      "heading_vi": "1. Người công bình giữa thời đại bại hoại",
      "scripture_refs": ["GEN.6.9", "GEN.6.14"],
      "narrative_vi": "Khi thế gian đầy dẫy sự hung bạo, Nô-ê vẫn là người công bình, trọn vẹn và đồng đi cùng Đức Chúa Trời. Ngài truyền cho ông đóng một chiếc tàu lớn bằng cây gô-phe...",
      "narrative_en": "In an age filled with violence, Noah walked faithfully with God and was commanded to build an ark of cypress wood...",
      "narrative_ja": "地が暴虐で満ちていた時代、ノアは正しい人であって、神と共に歩んでいた...",
      "illustration": {
        "asset_key": "biblical-story-ot-03-scene-01-building-ark-v1",
        "aspect_ratio": "16:9",
        "prompt_spec_id": "spec_ot_03_s01"
      },
      "key_terms": [
        {
          "vi": "giao ước",
          "en": "covenant",
          "ja": "契約",
          "ja_reading": "けいやく",
          "han_viet": "KHẾ ƯỚC",
          "strongs": "H1285",
          "orig_lemma": "בְּרִית (berith)",
          "lumilearn_jp_id": "lex_jp_keiyaku",
          "lumilearn_en_id": "lex_en_covenant"
        }
      ]
    }
  ],
  "reflection_questions": [
    "Vì sao Nô-ê kiên trì đóng tàu trên cạn dù người đương thời chưa từng thấy mưa lớn?",
    "Hình ảnh chiếc cầu vồng sau cơn mưa nhắc nhở điều gì về sự thành tín của Đức Chúa Trời?"
  ],
  "related_hymns": [42, 185]
}
```

---

## 4. Pipeline Sản xuất Minh họa Bút chì (Kế thừa `LumiLearnWeb_hoclieu`)

Áp dụng kiến trúc **Content-Addressed Media Manifest (`input_identity` $\to$ `output_sha256`)** từ `LumiLearnWeb_hoclieu/docs/learn-vi-shared-world-persona-media-plan.md`:

### 4.1. Quy tắc Mỹ thuật Bắt buộc (Visual Style Bible)
1. **Master Style Token**:
   - *"Masterpiece classical hand-drawn graphite and charcoal pencil illustration on warm ivory parchment paper (`#FAF7F0`), fine cross-hatching shading, expressive linework inspired by 19th-century biblical engravings and Rembrandt sketches, gentle chiaroscuro lighting, reverent and timeless atmosphere."*
2. **Quy tắc Cấm tuyệt đối (Negative Constraints)**:
   - **KHÔNG** vẽ bất kỳ chữ viết, ký tự, con số, tên riêng, câu Kinh Thánh, quốc kỳ hay watermark nào bên trong tranh (`no text, no typography, no letters, no numbers, no flags, no modern objects`). Nhờ đó một bức tranh dùng chung hoàn hảo cho mọi ngôn ngữ (Việt / Anh / Nhật).
3. **Tính Nhất quán Nhân vật & Bối cảnh (Shared Biblical Cast Registry)**:
   - Quản lý hồ sơ tạo hình nhân vật trong `media_manifest/biblical_cast.json` (ví dụ: `char_moses`, `char_david_youth`, `char_david_king`, `char_paul`, `loc_jerusalem_temple`, `loc_sea_of_galilee`) để các bức tranh giữa các câu chuyện giữ nguyên diện mạo, trang phục Trung Đông cổ đại và bối cảnh lịch sử.

### 4.2. Quản trị Bất biến & Lưu trữ (`media_manifest/`)
- Mỗi hình minh họa có một `asset_key` ngữ nghĩa cố định.
- Khi render ra WebP đa độ phân giải (`480w`, `960w`, `1440w`), tên file phát hành chứa hash nội dung hoặc quản lý qua manifest bất biến để CDN/Cloudflare Pages cache vĩnh viễn (`Cache-Control: public, max-age=31536000, immutable`).

