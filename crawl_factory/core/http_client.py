"""
Bộ khách HTTP lịch sự thế hệ 2 (`core/http_client.py`) — Tích hợp Chống Giới Hạn Thời Gian / Số Trang / Dung Lượng.

Tài liệu tham chiếu:
- `crawl_factory/sources/docs/technical-design-and-anti-blocking.md`

Giải quyết 5 Bẫy Giới Hạn Lưu Lượng & Phiên (Rate / Page-Window / Bandwidth Traps):
1. TRAP F1 — Nén Băng Thông `gzip/deflate` Tự Động (`Accept-Encoding: gzip, deflate`):
   - Giảm 80%–86% dung lượng tải trên đường truyền (ví dụ 1 chương `kinhthanh.httlvn.org` giảm từ ~72 KB
     xuống 10.3 KB; `getbible/vietnamese.json` giảm từ 13.2 MB xuống ~2.4 MB).
   - Tự động giải nén `Content-Encoding: gzip | deflate` trong `urllib.request` (tránh lỗi `UnicodeDecodeError: 0x8b`).
2. TRAP F2 — Vệ Sinh Cookie Phi Trạng Thái (Stateless Cookie Hygiene):
   - Trên `thanhca.httlvn.org`, mỗi bài hát trả về `Set-Cookie: thanh-ca_cookie=["1","2",...]`. Nếu dùng
     CookieJar tự động gửi lại cookie này qua 903 bài, header sẽ phình quá 8 KB gây lỗi `HTTP 400 Request Too Long`
     trên IIS 10.0 và bắt DB truy vấn lại toàn bộ lịch sử ở mỗi request!
   - `PoliteHttpClient` tuyệt đối KHÔNG lưu/gửi lại các cookie lịch sử (`thanh-ca_cookie`, `versions_used_recent`,
     `ASPSESSIONID*`), chỉ gửi đúng cookie cố định trong `config.json` (`version_current=VI1934`).
3. TRAP F3 — Giới Hạn Số Trang Theo Cửa Sổ Trượt (Sliding-Window Page Quota & Batch Cooldowns):
   - Cứ mỗi `batch_size` trang (mặc định 80 trang), crawler tự động nghỉ ngắn `batch_pause_seconds` (25–40s).
   - Cứ mỗi `macro_batch_size` trang (mặc định 300 trang), crawler tự động nghỉ dài `macro_pause_seconds` (90–120s)
     để xóa bộ đếm cửa sổ trượt (Sliding Window Counter) của IIS Dynamic IP Restrictions / Hostinger LiteSpeed.
4. TRAP F4 — Kiểm Soát Ngân Sách Dung Lượng (`max_mb_per_hour`) & Điều Tốc Thích Nghi AIMD:
   - Theo dõi tổng `wire_bytes` tải về và độ trễ phản hồi (`latency_ms`).
   - Nếu gặp `HTTP 429/503`, header `Retry-After`, hoặc độ trễ tăng vọt `> 3.0x` mức nền (dấu hiệu server đang
     bóp băng thông ngầm / soft-throttling), tự động nhân đôi `current_delay` (Additive/Multiplicative Increase)
     và chỉ giảm dần về `base_delay` sau 15 request thành công liên tiếp.
5. TRAP F5 — Hỗ Trợ Xoay Vòng Proxy (`ProxyRotator` tương thích `LumiLearnWeb_hoclieu` `proxy_pool.json`):
   - Cho phép truyền `--proxy-url` hoặc `--proxy-pool-file` để xoay IP khi cần.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional
import gzip
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib


class ContentValidationError(RuntimeError):
    """Ném ra khi phản hồi HTTP 200 nhưng thiếu chữ ký DOM bắt buộc hoặc dính trang Cloudflare."""


@dataclass
class HttpResponse:
    """Kết quả trả về từ `PoliteHttpClient` (body đã được giải nén tự động nếu server nén gzip/deflate)."""
    url: str
    final_url: str
    status: int
    headers: Dict[str, str]
    body: bytes
    wire_bytes: int
    elapsed_ms: float

    def text(self, encoding: str = "utf-8", errors: str = "replace") -> str:
        return self.body.decode(encoding, errors=errors)


class ProxyRotator:
    """
    Bộ quản lý và xoay vòng Proxy tương thích định dạng `state/proxy_pool.json` của `LumiLearnWeb_hoclieu`.
    """

    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies: List[str] = [p.strip() for p in (proxies or []) if p and p.strip()]
        self.index: int = 0

    @classmethod
    def from_file(cls, pool_path: Path | str, start_index: int = 0) -> "ProxyRotator":
        p = Path(pool_path)
        raw = json.loads(p.read_text(encoding="utf-8"))
        proxies = raw.get("proxies", []) if isinstance(raw, dict) else list(raw)
        rot = cls(proxies)
        if rot.proxies:
            rot.index = start_index % len(rot.proxies)
        return rot

    def current(self) -> Optional[str]:
        if not self.proxies:
            return None
        return self.proxies[self.index % len(self.proxies)]

    def rotate(self, reason: str = "") -> Optional[str]:
        if len(self.proxies) <= 1:
            return self.current()
        self.index = (self.index + 1) % len(self.proxies)
        nxt = self.current()
        print(f"[ProxyRotator] Xoay sang proxy #{self.index} ({nxt}) do: {reason}")
        return nxt


class PoliteHttpClient:
    """
    HTTP Client lịch sự thế hệ 2: nén băng thông gzip, vệ sinh cookie, nghỉ theo lô (Batch Cooldown),
    điều tốc thích nghi AIMD theo độ trễ server và giới hạn ngân sách MB/giờ.
    """

    def __init__(
        self,
        default_headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        delay_seconds: float = 1.0,
        jitter_seconds: float = 0.3,
        timeout_seconds: float = 25.0,
        max_retries: int = 4,
        batch_size: int = 80,
        batch_pause_seconds: float = 30.0,
        macro_batch_size: int = 300,
        macro_pause_seconds: float = 95.0,
        max_mb_per_hour: float = 120.0,
        proxy_rotator: Optional[ProxyRotator] = None,
    ):
        self.default_headers: Dict[str, str] = dict(default_headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
        })
        # Luôn bật nén gzip/deflate để giảm 80-86% dung lượng băng thông (TRAP F1)
        self.default_headers.setdefault("Accept-Encoding", "gzip, deflate")

        # Chỉ gửi các cookie cố định đã cấu hình, tuyệt đối không lưu cookie lịch sử phình to (TRAP F2)
        self.cookies: Dict[str, str] = dict(cookies or {})

        self.base_delay_seconds = float(delay_seconds)
        self.current_delay_seconds = float(delay_seconds)
        self.jitter_seconds = float(jitter_seconds)
        self.timeout_seconds = float(timeout_seconds)
        self.max_retries = int(max_retries)

        # Cấu hình chống giới hạn số trang theo cửa sổ trượt (Batch Cooldown - TRAP F3)
        self.batch_size = int(batch_size)
        self.batch_pause_seconds = float(batch_pause_seconds)
        self.macro_batch_size = int(macro_batch_size)
        self.macro_pause_seconds = float(macro_pause_seconds)

        # Ngân sách dung lượng đường truyền (Bandwidth Quota Guard - TRAP F4)
        self.max_mb_per_hour = float(max_mb_per_hour)
        self.proxy_rotator = proxy_rotator

        # Bộ đếm thống kê phiên chạy
        self._last_request_ts: float = 0.0
        self._session_start_ts: float = time.monotonic()
        self.total_requests: int = 0
        self.total_wire_bytes: int = 0
        self.total_uncompressed_bytes: int = 0
        self._success_streak: int = 0
        self._recent_latencies_ms: Deque[float] = deque(maxlen=20)

    def _enforce_quotas_and_sleep(self) -> None:
        """
        Thực thi 3 tầng bảo vệ trước mỗi request:
        1. Nghỉ theo lô trang (Batch Cooldown 80 trang / Macro Cooldown 300 trang).
        2. Kiểm tra ngân sách băng thông (MB/giờ).
        3. Nghỉ giữa 2 request liên tiếp theo `current_delay_seconds` (có điều tốc AIMD + Jitter).
        """
        # 1. Kiểm tra Batch Cooldown theo số trang đã tải trong phiên
        if self.total_requests > 0:
            if self.macro_batch_size > 0 and (self.total_requests % self.macro_batch_size == 0):
                pause = self.macro_pause_seconds * random.uniform(0.85, 1.15)
                print(
                    f"[QuotaGuard] Đã tải {self.total_requests} trang ({self.total_wire_bytes / 1048576:.2f} MB nén). "
                    f"Nghỉ dài {pause:.1f}s để xóa bộ đếm cửa sổ trượt (Macro Cooldown)..."
                )
                time.sleep(pause)
                self._last_request_ts = time.monotonic()
                return
            elif self.batch_size > 0 and (self.total_requests % self.batch_size == 0):
                pause = self.batch_pause_seconds * random.uniform(0.85, 1.15)
                print(
                    f"[QuotaGuard] Đã tải {self.total_requests} trang ({self.total_wire_bytes / 1048576:.2f} MB nén). "
                    f"Nghỉ ngắn {pause:.1f}s (Batch Cooldown)..."
                )
                time.sleep(pause)
                self._last_request_ts = time.monotonic()
                return

        # 2. Kiểm tra tốc độ tiêu thụ băng thông (MB/giờ)
        if self.max_mb_per_hour > 0 and self.total_wire_bytes > 5 * 1048576:
            elapsed_hours = max(1e-4, (time.monotonic() - self._session_start_ts) / 3600.0)
            current_mb = self.total_wire_bytes / 1048576.0
            projected_mb_per_hr = current_mb / elapsed_hours
            if projected_mb_per_hr > self.max_mb_per_hour:
                extra_sleep = min(15.0, (projected_mb_per_hr / self.max_mb_per_hour - 1.0) * 5.0)
                print(
                    f"[QuotaGuard] Tốc độ băng thông hiện tại ({projected_mb_per_hr:.1f} MB/h) vượt ngưỡng "
                    f"{self.max_mb_per_hour:.1f} MB/h -> tự động hãm nhịp {extra_sleep:.1f}s."
                )
                time.sleep(extra_sleep)

        # 3. Khoảng nghỉ lịch sự giữa 2 request liên tiếp
        if self._last_request_ts > 0 and self.current_delay_seconds > 0:
            elapsed = time.monotonic() - self._last_request_ts
            target_wait = max(
                0.1,
                self.current_delay_seconds + random.uniform(-self.jitter_seconds, self.jitter_seconds),
            )
            if elapsed < target_wait:
                time.sleep(target_wait - elapsed)

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = dict(self.default_headers)
        if self.cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
            headers["Cookie"] = cookie_str
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @staticmethod
    def _decompress_body(raw_bytes: bytes, content_encoding: str) -> bytes:
        """Tự động giải nén `gzip` hoặc `deflate` nếu server trả về luồng nén (TRAP F1)."""
        enc = (content_encoding or "").lower()
        if not raw_bytes:
            return raw_bytes
        if "gzip" in enc or (len(raw_bytes) >= 2 and raw_bytes[:2] == b"\x1f\x8b"):
            try:
                return gzip.decompress(raw_bytes)
            except Exception:
                return raw_bytes
        if "deflate" in enc:
            try:
                return zlib.decompress(raw_bytes)
            except zlib.error:
                try:
                    return zlib.decompress(raw_bytes, -zlib.MAX_WBITS)
                except Exception:
                    return raw_bytes
        return raw_bytes

    def _record_latency_and_adapt_delay(self, elapsed_ms: float) -> None:
        """
        Điều tốc thích nghi AIMD (Additive Increase / Multiplicative Decrease) dựa trên độ trễ server:
        Nếu độ trễ request hiện tại vọt lên > 3.2 lần trung bình của 10 request trước đó (và > 2500ms),
        tự động tăng nhẹ `current_delay_seconds` để giảm tải cho server gốc.
        """
        if len(self._recent_latencies_ms) >= 6:
            avg_ms = sum(self._recent_latencies_ms) / len(self._recent_latencies_ms)
            if elapsed_ms > max(2800.0, avg_ms * 3.2):
                old_d = self.current_delay_seconds
                self.current_delay_seconds = min(self.base_delay_seconds * 4.0, self.current_delay_seconds * 1.4 + 0.3)
                self._success_streak = 0
                print(
                    f"[AIMD] Phát hiện độ trễ server tăng cao ({elapsed_ms:.0f}ms vs trung bình {avg_ms:.0f}ms). "
                    f"Tự động tăng delay: {old_d:.2f}s -> {self.current_delay_seconds:.2f}s"
                )
                self._recent_latencies_ms.append(elapsed_ms)
                return

        self._recent_latencies_ms.append(elapsed_ms)
        self._success_streak += 1
        if self._success_streak >= 15 and self.current_delay_seconds > self.base_delay_seconds:
            self.current_delay_seconds = max(self.base_delay_seconds, self.current_delay_seconds - 0.2)
            self._success_streak = 0

    def _build_opener(self) -> urllib.request.OpenerDirector:
        """Tạo opener (có gắn ProxyHandler nếu `proxy_rotator` đang bật, không gắn HTTPCookieProcessor để giữ Stateless Cookie)."""
        handlers = []
        if self.proxy_rotator and self.proxy_rotator.current():
            proxy_url = self.proxy_rotator.current()
            handlers.append(urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
        return urllib.request.build_opener(*handlers)

    def request(
        self,
        url: str,
        method: str = "GET",
        form_data: Optional[Dict[str, str]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        expected_signatures: Optional[Iterable[str]] = None,
        allow_404: bool = False,
    ) -> HttpResponse:
        """
        Thực hiện HTTP GET/POST với đầy đủ bảo vệ Rate-limit, Batch Cooldown, Gzip Decompression và Retry.
        """
        headers = self._build_headers(extra_headers)
        payload_bytes: Optional[bytes] = None
        if form_data is not None:
            payload_bytes = urllib.parse.urlencode(form_data).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            self._enforce_quotas_and_sleep()
            req = urllib.request.Request(url, data=payload_bytes, headers=headers, method=method.upper())
            opener = self._build_opener()
            t0 = time.monotonic()
            try:
                with opener.open(req, timeout=self.timeout_seconds) as resp:
                    self._last_request_ts = time.monotonic()
                    elapsed_ms = (self._last_request_ts - t0) * 1000.0
                    raw_wire_bytes = resp.read()
                    resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                    status = resp.status or 200
                    final_url = resp.geturl()

                wire_len = len(raw_wire_bytes)
                body = self._decompress_body(raw_wire_bytes, resp_headers.get("content-encoding", ""))
                self.total_requests += 1
                self.total_wire_bytes += wire_len
                self.total_uncompressed_bytes += len(body)

                # Kiểm tra xem có bị dính trang Cloudflare Challenge hay Soft-Block không
                head_sample = body[:4096].decode("utf-8", errors="ignore")
                if "<title>Just a moment...</title>" in head_sample or "cf-chl-bypass" in head_sample:
                    raise ContentValidationError(f"Dính Cloudflare Challenge tại URL: {url}")

                if expected_signatures:
                    full_text = body.decode("utf-8", errors="ignore")
                    for sig in expected_signatures:
                        if sig not in full_text:
                            raise ContentValidationError(
                                f"Phản hồi từ {url} thiếu chữ ký DOM bắt buộc: {sig!r}"
                            )

                self._record_latency_and_adapt_delay(elapsed_ms)
                return HttpResponse(
                    url=url,
                    final_url=final_url,
                    status=status,
                    headers=resp_headers,
                    body=body,
                    wire_bytes=wire_len,
                    elapsed_ms=elapsed_ms,
                )

            except urllib.error.HTTPError as e:
                self._last_request_ts = time.monotonic()
                if e.code == 404 and allow_404:
                    self.total_requests += 1
                    return HttpResponse(
                        url=url,
                        final_url=url,
                        status=404,
                        headers={k.lower(): v for k, v in e.headers.items()} if e.headers else {},
                        body=b"",
                        wire_bytes=0,
                        elapsed_ms=(self._last_request_ts - t0) * 1000.0,
                    )
                last_exc = e
                if e.code in (403, 429, 500, 502, 503, 504) and attempt < self.max_retries:
                    self._success_streak = 0
                    retry_after_hdr = e.headers.get("Retry-After") if e.headers else None
                    wait_sec = 0.0
                    if retry_after_hdr and retry_after_hdr.isdigit():
                        wait_sec = float(retry_after_hdr)
                    else:
                        wait_sec = (self.current_delay_seconds or 1.0) * (2.5 ** (attempt + 1)) + random.uniform(2.0, 6.0)

                    # Nhân đôi current_delay khi gặp 429 hoặc 503
                    if e.code in (429, 503):
                        self.current_delay_seconds = min(
                            max(10.0, self.base_delay_seconds * 5.0),
                            self.current_delay_seconds * 1.8 + 1.0,
                        )
                    if self.proxy_rotator:
                        self.proxy_rotator.rotate(reason=f"HTTP {e.code}")

                    print(
                        f"[PoliteHttpClient] HTTP {e.code} tại {url} -> nghỉ {wait_sec:.1f}s "
                        f"(delay mới={self.current_delay_seconds:.2f}s, thử lại {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_sec)
                    continue
                raise

            except (urllib.error.URLError, TimeoutError, ContentValidationError) as e:
                self._last_request_ts = time.monotonic()
                last_exc = e
                if attempt < self.max_retries:
                    self._success_streak = 0
                    if self.proxy_rotator:
                        self.proxy_rotator.rotate(reason=type(e).__name__)
                    backoff = (self.current_delay_seconds or 1.0) * (2.0 ** (attempt + 1)) + random.uniform(1.0, 4.0)
                    print(
                        f"[PoliteHttpClient] Lỗi {type(e).__name__} ({e}) tại {url} -> "
                        f"nghỉ {backoff:.1f}s (thử lại {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff)
                    continue
                raise

        assert last_exc is not None
        raise last_exc
