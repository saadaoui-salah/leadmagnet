"""
Example spider showing how to use the proxy middleware.

Usage:
    # Default session (round-robin, any country):
    scrapy crawl example

    # With specific session:
    scrapy crawl example -a session=premium

    # Override rotation per-request:
    class MySpider(scrapy.Spider):
        proxy_session = "premium"
        proxy_rotation = "random"
        proxy_location = "US"
"""

import scrapy


class ProxyExampleSpider(scrapy.Spider):
    name = "proxy_example"
    start_urls = ["https://ipv4.webshare.io/"]

    # ── Class-level proxy config (optional) ────────────────────────────
    # These override settings.py defaults per-spider.
    # Set proxy_provider = "none" to disable proxies for this spider.

    # proxy_provider = "webshare"    # "webshare" | "oxylabs" | "none"
    # proxy_session = "default"      # which named session pool to use
    # proxy_rotation = "round-robin" # round-robin | random | least-used
    # proxy_location = "US"          # override country filter
    # proxy_mode = "direct"          # direct | backbone

    def parse(self, response):
        self.logger.info("Response from: %s", response.url)
        self.logger.info("IP shown: %s", response.text.strip())
        yield {
            "url": response.url,
            "ip": response.text.strip(),
            "status": response.status,
        }
