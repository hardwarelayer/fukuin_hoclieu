"""
Gói lõi (Core Framework) của `fukuin_hoclieu/crawl_factory`.

Cung cấp 4 module nền tảng dùng chung cho mọi nguồn thu thập dữ liệu:
1. `usfm_books`: Bảng chuẩn hóa 66 sách Kinh Thánh đa nguồn (USFM 3.0 <-> HTTLVN <-> TinLanh.com <-> GetBible <-> WLC/MorphGNT).
2. `text_normalizer`: Bộ xử lý Unicode NFC, sửa lỗi ký tự Eth `Ð` (`U+00D0`), khôi phục lỗi Double-UTF8 Mojibake và chuẩn hóa đường dẫn media.
3. `state_manager`: Quản lý trạng thái tiến độ (`state/*.json`) và ghi file thô (`raw/`) theo cơ chế nguyên tử (Atomic Write) kèm bắt tín hiệu `Ctrl+C` (Graceful Shutdown).
4. `http_client`: Bộ khách HTTP lịch sự (Polite HTTP Client) có delay + jitter, exponential backoff, kiểm tra chữ ký DOM và phát hiện Cloudflare challenge.
"""

