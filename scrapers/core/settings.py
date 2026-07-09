# Scrapy settings for core project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv

# Load .env file (all credentials come from here)
load_dotenv()

BOT_NAME = "core"

SPIDER_MODULES = ["core.spiders"]
NEWSPIDER_MODULE = "core.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "core (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 15
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403]

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 3
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# ── Spider Middlewares ───────────────────────────────────────────────────
SPIDER_MIDDLEWARES = {
    "core.cost_calculator.ProxyCostCalculatorMiddleware": 500,
}

DOWNLOADER_MIDDLEWARES = {
    "core.middlewares.CurlCffiDownloaderMiddleware": 400,
    "core.proxy_retry_middleware.ProxyRetryMiddleware": 401,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,  # replaced by our middleware
}

# ── Credentials (loaded from .env) ───────────────────────────────────────
# Zyte API
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY", "")
ZYTE_PROJECT_ID = os.getenv("ZYTE_PROJECT_ID", "")

# Webshare Proxy
WEBSHARE_API_TOKEN = os.getenv("WEBSHARE_API_TOKEN", "")

# Oxylabs Proxy
OXYLABS_HOST = os.getenv("OXYLABS_HOST", "dc.oxylabs.io")
OXYLABS_PORT = int(os.getenv("OXYLABS_PORT", "8000"))
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME", "")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD", "")

# ── Proxy Configuration ──────────────────────────────────────────────────
# Auto-enable if provider is set (override with PROXY_ENABLED=False to disable)
PROXY_PROVIDER = os.getenv("PROXY_PROVIDER", "")  # "webshare" | "oxylabs" | ""
PROXY_ENABLED = bool(PROXY_PROVIDER.strip())

# Proxy provider: "webshare" | "oxylabs" | "static"
PROXY_PROVIDER = "webshare"

# Proxy type for pricing: "datacenter" | "residential" | "static_residential" | "isp" | "dedicated_datacenter"
PROXY_TYPE = "datacenter"

# Cost tracking overrides (optional — if not set, uses provider defaults)
# PROXY_COST_MODEL = "per_gb"            # per_gb | per_ip_monthly | per_request
# PROXY_COST_RESIDENTIAL_PER_GB = 6.00   # $/GB for residential
# PROXY_COST_DATACENTER_PER_IP = 1.20    # $/IP/month for datacenter

# Rotation strategy: "round-robin" | "random" | "least-used"
PROXY_ROTATION = "round-robin"

# Country filter — ISO 3166-1 alpha-2 codes, comma-separated.
# "ZZ" = any country, "US" = United States only, "US,GB" = US or UK.
PROXY_LOCATION = "ZZ"

# Proxy mode: "direct" (unique IPs per proxy) or "backbone" (single gateway, rotating IP)
PROXY_MODE = "direct"

# Specific Webshare plan ID (optional — omit to use default plan)
# PROXY_PLAN_ID = 1234

# Seconds between API refreshes (proxies are cached locally)
PROXY_REFRESH_INTERVAL = 300

# Named sessions — each session has its own proxy pool and strategy.
# Spiders set proxy_session = "session_name" to pick one.
PROXY_SESSIONS = {
    "default": {
        "strategy": "round-robin",
        "country": "ZZ",
        "mode": "direct",
    },
    # "premium": {
    #     "strategy": "random",
    #     "country": "US",
    #     "mode": "direct",
    # },
    # "scraping": {
    #     "strategy": "least-used",
    #     "country": "US,GB,CA",
    #     "mode": "backbone",
    # },
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "core.pipelines.DjangoUploadPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

FEEDS = {
    "output/zillow_%(time)s.json": {
        "format": "json",
        "overwrite": True,
    },
}
