#!/usr/bin/env python3
"""
CLI Điều Phối Trung Tâm của Nhà Máy Thu Thập Dữ Liệu (`fukuin_hoclieu/crawl_factory/run_crawler.py`).

Hướng dẫn sử dụng cho đội dự án:
--------------------------------
1. Kiểm thử nhanh (Smoke Test 2 chương Kinh Thánh từ `kinhthanh.httlvn.org`):
   python -X utf8 crawl_factory/run_crawler.py --source kinhthanh_httlvn --step all --limit 2

2. Kiểm thử chương có Bẫy Runtime cụ thể (ví dụ Ma-thi-ơ 17 có câu 21 khuyết, hoặc Thi-thiên 51 có Thượng đề):
   python -X utf8 crawl_factory/run_crawler.py --source kinhthanh_httlvn --step all --book MAT --chapter 17
   python -X utf8 crawl_factory/run_crawler.py --source open_multilingual --step all --book PSA --chapter 51

3. Đối chiếu 3 nguồn (3-Way Majority Voting) giữa HTTLVN, TinLanh.com và GetBible:
   python -X utf8 crawl_factory/run_crawler.py --source tinlanh_com --step all --book PSA --chapter 23

4. Kiểm thử 2 bài Thánh Ca & KTĐĐ từ `thanhca.httlvn.org`:
   python -X utf8 crawl_factory/run_crawler.py --source thanhca_httlvn --step all --limit 2

5. Chạy thu thập toàn bộ (do người vận hành chạy trong Terminal riêng, hỗ trợ nhấn Ctrl+C tạm dừng & chạy tiếp):
   python -X utf8 crawl_factory/run_crawler.py --source kinhthanh_httlvn --step all
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

# Đảm bảo import được gói `crawl_factory` dù gọi từ thư mục gốc `fukuin_hoclieu` hay từ trong `crawl_factory/`
CRAWL_FACTORY_DIR = Path(__file__).resolve().parent
REPO_ROOT_DIR = CRAWL_FACTORY_DIR.parent
if str(REPO_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DIR))

from crawl_factory.core.http_client import ProxyRotator
from crawl_factory.sources.kinhthanh_httlvn.crawler import KinhthanhHttlvnCrawler
from crawl_factory.sources.open_multilingual.ingestor import OpenMultilingualIngestor
from crawl_factory.sources.thanhca_httlvn.crawler import ThanhcaHttlvnCrawler
from crawl_factory.sources.tinlanh_com.crawler import TinlanhComCrawler
from crawl_factory.sources.vietchristian.crawler import VietchristianCrawler


def load_config() -> dict:
    cfg_path = CRAWL_FACTORY_DIR / "config.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CLI điều phối thu thập và chuẩn hóa dữ liệu cho fukuin_hoclieu/crawl_factory."
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["kinhthanh_httlvn", "tinlanh_com", "thanhca_httlvn", "vietchristian", "open_multilingual"],
        help="Nguồn dữ liệu cần thực thi.",
    )
    parser.add_argument(
        "--step",
        default="all",
        choices=["1", "2", "3", "all"],
        help="Bước thực thi: 1 (Init Queue / Discovery), 2 (Fetch Raw), 3 (Parse & Verify), hoặc all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số lượng chương/mục cần tải (luôn dùng --limit 2 khi chạy smoke test).",
    )
    parser.add_argument(
        "--book",
        type=str,
        default=None,
        help="Chỉ lọc 1 sách Kinh Thánh (chấp nhận mã USFM như GEN, PSA, MAT hoặc mã HTTLVN như sa, thi, mat).",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        default=None,
        help="Chỉ lọc 1 số chương cụ thể (ví dụ: --book MAT --chapter 17).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bắt buộc tải lại từ mạng ngay cả khi file đã có trong raw/.",
    )
    parser.add_argument(
        "--skip-musicxml",
        action="store_true",
        help="(Chỉ dùng cho thanhca_httlvn) Bỏ qua tải file MusicXML 75KB để chỉ tải nhanh HTML lời/hợp âm (~5KB gzip).",
    )
    parser.add_argument(
        "--proxy-url",
        type=str,
        default=None,
        help="Pin 1 địa chỉ HTTP/HTTPS proxy cố định (ví dụ: http://1.2.3.4:8080).",
    )
    parser.add_argument(
        "--proxy-pool-file",
        type=str,
        default=None,
        help="Đường dẫn tới file proxy_pool.json (tương thích LumiLearnWeb_hoclieu) để xoay vòng IP tự động.",
    )

    args = parser.parse_args()
    config = load_config()

    proxy_rotator = None
    if args.proxy_url:
        proxy_rotator = ProxyRotator([args.proxy_url])
    elif args.proxy_pool_file:
        proxy_rotator = ProxyRotator.from_file(args.proxy_pool_file)

    if args.source == "kinhthanh_httlvn":
        crawler = KinhthanhHttlvnCrawler(CRAWL_FACTORY_DIR, config)
        crawler.client.proxy_rotator = proxy_rotator
        if args.step in ("1", "all"):
            crawler.step_1_init_queue()
        if args.step in ("2", "all"):
            crawler.step_2_fetch_raw(
                limit=args.limit,
                filter_book=args.book,
                filter_chapter=args.chapter,
                force=args.force,
            )
        if args.step in ("3", "all"):
            crawler.step_3_parse_normalized(
                limit=args.limit,
                filter_book=args.book,
                filter_chapter=args.chapter,
            )

    elif args.source == "tinlanh_com":
        crawler = TinlanhComCrawler(CRAWL_FACTORY_DIR, config, proxy_rotator=proxy_rotator)
        if args.step in ("1", "all"):
            crawler.step_1_init_queue()
        if args.step in ("2", "all"):
            crawler.step_2_fetch_raw(
                limit=args.limit,
                filter_book=args.book,
                filter_chapter=args.chapter,
                force=args.force,
            )
        if args.step in ("3", "all"):
            crawler.step_3_parse_and_verify_3way(
                limit=args.limit,
                filter_book=args.book,
                filter_chapter=args.chapter,
            )

    elif args.source == "thanhca_httlvn":
        crawler = ThanhcaHttlvnCrawler(CRAWL_FACTORY_DIR, config)
        crawler.client.proxy_rotator = proxy_rotator
        if args.step in ("1", "all"):
            crawler.step_1_init_queue(discover_mp3_playlist=True)
        if args.step in ("2", "all"):
            crawler.step_2_fetch_raw(
                limit=args.limit,
                fetch_musicxml=not args.skip_musicxml,
                force=args.force,
            )
        if args.step in ("3", "all"):
            crawler.step_3_parse_normalized(limit=args.limit)

    elif args.source == "vietchristian":
        crawler = VietchristianCrawler(CRAWL_FACTORY_DIR, config)
        crawler.client.proxy_rotator = proxy_rotator
        if args.step in ("1", "all"):
            crawler.step_1_init_queue()
        if args.step in ("2", "all"):
            crawler.step_2_fetch_raw(limit=args.limit, force=args.force)
        if args.step in ("3", "all"):
            crawler.step_3_parse_normalized()

    elif args.source == "open_multilingual":
        ingestor = OpenMultilingualIngestor(CRAWL_FACTORY_DIR, config)
        ingestor.client.proxy_rotator = proxy_rotator
        ingestor.run_pipeline(
            limit=args.limit,
            filter_book=args.book,
            filter_chapter=args.chapter,
            include_sanbika=(args.book is None),
            force=args.force,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

