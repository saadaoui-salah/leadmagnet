"""
Proxy Retry Middleware — handles proxy rotation on blocked requests.

Replaces Scrapy's built-in retry middleware with proxy-aware retry.
When a request gets 403/429/503, rotates proxy AND retries.

Usage in settings.py:
    DOWNLOADER_MIDDLEWARES = {
        "core.proxy_retry_middleware.ProxyRetryMiddleware": 400,
        "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,  # disable default
    }
"""

import logging
from scrapy import signals
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class ProxyRetryMiddleware:
    """Retry middleware that rotates proxy on each retry."""

    def __init__(self, settings):
        self.max_retry_times = settings.getint("RETRY_TIMES", 15)
        self.retry_http_codes = set(settings.getlist("RETRY_HTTP_CODES", [500, 502, 503, 504, 522, 524, 408, 429]))
        self.proxy_enabled = settings.getbool("PROXY_ENABLED", False)
        self._proxy_mgr = None

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls(crawler.settings)
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def spider_opened(self, spider):
        # Lazy import to avoid circular imports
        from core.proxy_manager import ProxyManager

        if self.proxy_enabled:
            try:
                self._proxy_mgr = ProxyManager.from_settings(spider.crawler.settings)
                self._proxy_mgr.refresh(force=True)
            except Exception as e:
                logger.warning("Proxy manager init failed: %s", e)

    def _get_new_proxy(self, spider):
        """Get a new proxy for retry."""
        if not self._proxy_mgr:
            return None

        session = getattr(spider, "proxy_session", "default")
        proxy = self._proxy_mgr.get_proxy(session=session)
        return proxy.url if proxy else None

    def _mark_proxy_bad(self, proxy_url, spider):
        """Mark current proxy as bad."""
        if not self._proxy_mgr or not proxy_url:
            return

        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)
        if parsed.hostname:
            proxy_addr = f"{parsed.hostname}:{parsed.port}"
            session = getattr(spider, "proxy_session", "default")
            self._proxy_mgr.mark_bad(proxy_addr, session=session)
            logger.warning("Proxy %s marked as bad", proxy_addr)

    def process_response(self, request, response, spider):
        """Handle responses - rotate proxy on blocked status."""
        if response.status in self.retry_http_codes:
            reason = f"{response.status} Forbidden"

            # Get retry count
            retry_times = request.meta.get("retry_times", 0) + 1

            if retry_times <= self.max_retry_times:
                # Mark current proxy as bad
                current_proxy = request.meta.get("proxy")
                self._mark_proxy_bad(current_proxy, spider)

                # Get new proxy
                new_proxy = self._get_new_proxy(spider)

                # Set retry meta
                request.meta["retry_times"] = retry_times
                request.meta["proxy"] = new_proxy

                if new_proxy:
                    from urllib.parse import urlparse
                    parsed = urlparse(new_proxy)
                    logger.info(
                        "Retrying %s (retry %d/%d) with new proxy %s",
                        request.url, retry_times, self.max_retry_times, parsed.hostname
                    )
                else:
                    logger.info(
                        "Retrying %s (retry %d/%d) with no proxy",
                        request.url, retry_times, self.max_retry_times
                    )

                return request.dont_filter(True)  # Re-schedule request

        return response

    def process_exception(self, request, exception, spider):
        """Handle connection errors - rotate proxy."""
        retry_times = request.meta.get("retry_times", 0) + 1

        if retry_times <= self.max_retry_times:
            # Mark current proxy as bad
            current_proxy = request.meta.get("proxy")
            self._mark_proxy_bad(current_proxy, spider)

            # Get new proxy
            new_proxy = self._get_new_proxy(spider)

            request.meta["retry_times"] = retry_times
            request.meta["proxy"] = new_proxy

            logger.info(
                "Retrying %s after exception (retry %d/%d)",
                request.url, retry_times, self.max_retry_times
            )
            return request.dont_filter(True)

        return None
