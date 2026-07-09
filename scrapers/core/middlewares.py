import asyncio
import time

from curl_cffi import requests as curl_requests
from scrapy.http import TextResponse
from scrapy import signals

from core.browser_profiles import get_random_profile
from core.proxy_manager import ProxyManager, WebshareProxyManager


class CurlCffiDownloaderMiddleware:
    """
    Downloader middleware using curl_cffi to bypass bot detection.

    Proxy support is built-in. Configure via settings.py:

        WEBSHARE_API_TOKEN = "your-token"
        PROXY_ENABLED = True
        PROXY_ROTATION = "round-robin"   # round-robin | random | least-used
        PROXY_LOCATION = "ZZ"            # ZZ = any, US, GB, etc.
        PROXY_MODE = "direct"            # direct | backbone
        PROXY_SESSIONS = {               # named sessions with own pools
            "default": {"strategy": "round-robin", "country": "ZZ", "mode": "direct"},
            "premium": {"strategy": "random", "country": "US", "mode": "direct"},
        }

    Or set class variables on the spider:

        class MySpider(scrapy.Spider):
            proxy_session = "premium"
            proxy_rotation = "random"
            proxy_location = "US"
    """

    def __init__(self, timeout=30, proxy_enabled=False):
        self.timeout = timeout
        self.proxy_enabled = proxy_enabled
        self._last_request_time = 0
        self._proxy_mgr: ProxyManager | None = None

    @classmethod
    def from_crawler(cls, crawler):
        proxy_enabled = crawler.settings.getbool("PROXY_ENABLED", False)

        mw = cls(
            timeout=crawler.settings.getint("CURL_CFFI_TIMEOUT", 30),
            proxy_enabled=proxy_enabled,
        )
        mw._download_delay = crawler.settings.getfloat("DOWNLOAD_DELAY", 0)

        if proxy_enabled:
            try:
                mw._proxy_mgr = ProxyManager.from_settings(crawler.settings)
                mw._proxy_mgr.refresh(force=True)
            except ValueError as e:
                proxy_enabled = False
                import logging
                logging.warning("Proxy manager init failed: %s", e)

        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def spider_opened(self, spider):
        if self.proxy_enabled and self._proxy_mgr:
            stats = self._proxy_mgr.stats()
            total = sum(s["total"] for s in stats.values())
            spider.logger.info(
                "CurlCffiDownloaderMiddleware enabled (proxies: %d loaded)", total
            )
        else:
            spider.logger.info("CurlCffiDownloaderMiddleware enabled (no proxies)")

    def _get_proxy_for_request(self, spider):
        """Resolve which proxy to use based on spider class variables or defaults."""
        # Spider can disable proxies per-spider
        spider_provider = getattr(spider, "proxy_provider", None)
        if spider_provider == "none":
            return None
        if not self.proxy_enabled or not self._proxy_mgr:
            return None

        # Spider can override session/rotation/location/type via class vars
        session = getattr(spider, "proxy_session", "default")
        rotation = getattr(spider, "proxy_rotation", None)
        location = getattr(spider, "proxy_location", None)
        proxy_type = getattr(spider, "proxy_type", None)

        # Dynamic override: if spider sets proxy_rotation, proxy_location, or proxy_type,
        # rebuild the session config on the fly
        if rotation or location or proxy_type:
            mgr = self._proxy_mgr
            cfg = mgr.sessions.get(session, {}).copy()
            if rotation:
                cfg["strategy"] = rotation
            if location:
                cfg["country"] = location
            if proxy_type:
                cfg["proxy_type"] = proxy_type
                # Map proxy_type to Webshare mode
                if proxy_type == "backbone":
                    cfg["mode"] = "backbone"
                elif proxy_type in ("datacenter", "static_residential", "residential"):
                    cfg["mode"] = "direct"
            mgr.sessions[session] = cfg
            mgr._build_iterator(session)

        if rotation == "random" or location:
            return self._proxy_mgr.get_random_proxy(session=session)
        return self._proxy_mgr.get_proxy(session=session)

    def process_response(self, request, response, spider):
        """Check response for blocking indicators and mark proxy as bad if needed."""
        if not self.proxy_enabled or not self._proxy_mgr:
            return response

        # Check if response indicates blocking
        blocked_status = {403, 429, 503}
        if response.status in blocked_status:
            proxy = request.meta.get("proxy")
            if proxy and self._proxy_mgr:
                session = getattr(spider, "proxy_session", "default")
                # Extract proxy ID from URL
                from urllib.parse import urlparse
                parsed = urlparse(proxy)
                proxy_id = f"{parsed.hostname}:{parsed.port}"
                self._proxy_mgr.mark_bad(proxy_id, session=session)
                spider.logger.warning(
                    "Proxy %s blocked (status %d), rotating", proxy_id, response.status
                )

        return response

    async def process_request(self, request, spider):
        if not request.url.startswith("http"):
            return None

        if self._download_delay > 0 and self._last_request_time > 0:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self._download_delay:
                wait = self._download_delay - elapsed
                spider.logger.debug("DOWNLOAD_DELAY: waiting %.1fs", wait)
                await asyncio.sleep(wait)

        profile = get_random_profile()

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

        # ── Resolve proxy ──────────────────────────────────────────────
        proxy = self._get_proxy_for_request(spider)
        proxy_kwargs = {}
        if proxy:
            proxy_kwargs["proxies"] = proxy.as_dict
            spider.logger.debug("Using proxy: %s", proxy.proxy_address)

        try:
            resp = curl_requests.request(
                method=request.method,
                url=request.url,
                headers=headers,
                cookies=cookies,
                data=request.body if request.body else None,
                timeout=self.timeout,
                impersonate=profile["impersonate"],
                allow_redirects=True,
                **proxy_kwargs,
            )
        except Exception as e:
            spider.logger.error("curl_cffi error: %s", e)
            # Mark proxy as bad if it failed
            if proxy and self._proxy_mgr:
                self._proxy_mgr.mark_bad(proxy.id, session=getattr(spider, "proxy_session", "default"))
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
