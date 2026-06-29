import asyncio
import time

from curl_cffi import requests as curl_requests
from scrapy.http import TextResponse
from scrapy import signals


class CurlCffiDownloaderMiddleware:
    """Downloader middleware using curl_cffi to bypass bot detection."""

    def __init__(self, timeout=30, impersonate="chrome"):
        self.timeout = timeout
        self.impersonate = impersonate
        self._last_request_time = 0

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls(
            timeout=crawler.settings.getint("CURL_CFFI_TIMEOUT", 30),
            impersonate=crawler.settings.get("CURL_CFFI_IMPERSONATE", "chrome"),
        )
        mw._download_delay = crawler.settings.getfloat("DOWNLOAD_DELAY", 0)
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def spider_opened(self, spider):
        spider.logger.info("CurlCffiDownloaderMiddleware enabled (impersonate=%s)", self.impersonate)

    async def process_request(self, request, spider):
        if not request.url.startswith("http"):
            return None

        # Apply download delay (middleware returns response directly, bypassing downloader)
        if self._download_delay > 0 and self._last_request_time > 0:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self._download_delay:
                wait = self._download_delay - elapsed
                spider.logger.debug("DOWNLOAD_DELAY: waiting %.1fs", wait)
                await asyncio.sleep(wait)

        headers = {}
        for k, v in request.headers.items():
            key = k.decode() if isinstance(k, bytes) else str(k)
            if isinstance(v, list):
                val = v[0].decode() if isinstance(v[0], bytes) else str(v[0])
            elif isinstance(v, bytes):
                val = v.decode()
            else:
                val = str(v)
            headers[key] = val

        cookies = {}
        if hasattr(request, "cookies") and request.cookies:
            if isinstance(request.cookies, dict):
                cookies = request.cookies
            else:
                for c in request.cookies:
                    cookies[c.get("name", "")] = c.get("value", "")

        try:
            resp = curl_requests.request(
                method=request.method,
                url=request.url,
                headers=headers,
                cookies=cookies,
                data=request.body if request.body else None,
                timeout=self.timeout,
                impersonate=self.impersonate,
                allow_redirects=True,
            )
        except Exception as e:
            spider.logger.error("curl_cffi error: %s", e)
            return None

        self._last_request_time = time.monotonic()

        scrapy_resp = TextResponse(
            url=resp.url,
            status=resp.status_code,
            headers=dict(resp.headers),
            body=resp.content,
            encoding="utf-8",
            request=request,
        )

        return scrapy_resp
