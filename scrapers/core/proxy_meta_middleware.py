"""
Proxy Meta Middleware — injects proxy URL into request.meta['proxy'].

This middleware is simpler than CurlCffiDownloaderMiddleware and works
with Scrapy's built-in proxy handling via request.meta['proxy'].

Usage in settings.py:
    DOWNLOADER_MIDDLEWARES = {
        "core.proxy_meta_middleware.ProxyMetaMiddleware": 400,
    }

Or use both middlewares:
    DOWNLOADER_MIDDLEWARES = {
        "core.middlewares.CurlCffiDownloaderMiddleware": 400,
        "core.proxy_meta_middleware.ProxyMetaMiddleware": 401,
    }

Spider class variables:
    proxy_provider = "webshare"  # "webshare" | "oxylabs" | "none"
    proxy_session = "default"
    proxy_rotation = "round-robin"
    proxy_location = "US"
"""

import os
from core.proxy_manager import ProxyManager


class ProxyMetaMiddleware:
    """
    Downloader middleware that injects proxy URL into request.meta['proxy'].

    Use with Scrapy's built-in HttpProxyMiddleware or your own proxy handling.
    """

    def __init__(self, proxy_enabled=False):
        self.proxy_enabled = proxy_enabled
        self._proxy_mgr = None

    @classmethod
    def from_crawler(cls, crawler):
        proxy_enabled = crawler.settings.getbool("PROXY_ENABLED", False)

        mw = cls(proxy_enabled=proxy_enabled)

        if proxy_enabled:
            try:
                mw._proxy_mgr = ProxyManager.from_settings(crawler.settings)
                mw._proxy_mgr.refresh(force=True)
            except ValueError as e:
                proxy_enabled = False
                import logging
                logging.warning("ProxyMetaMiddleware init failed: %s", e)

        return mw

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

    def process_request(self, request, spider):
        """Inject proxy URL into request.meta['proxy']."""
        proxy = self._get_proxy_for_request(spider)
        if proxy:
            request.meta["proxy"] = proxy.url
            spider.logger.debug("Injected proxy: %s", proxy.proxy_address)
        return None
