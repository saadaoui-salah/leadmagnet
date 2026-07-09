"""
Proxy Cost Calculator Middleware — tracks bandwidth and displays cost in finished stats.

Calculates cost based on provider pricing and adds stats to spider closure.

Stats displayed:
    proxy/provider            — which provider was used
    proxy/requests            — total requests made
    proxy/bandwidth_bytes     — total bandwidth in bytes
    proxy/bandwidth_mb        — total bandwidth in megabytes
    proxy/cost_estimate       — estimated cost in USD
    proxy/cost_per_request    — average cost per request
    proxy/cost_per_mb         — average cost per megabyte

Pricing (2026):
    Webshare:
        Datacenter:        $0.00/proxy/month (unlimited BW)
        Static Residential: $0.30/proxy/month
        Rotating Residential: $3.50/GB

    Oxylabs:
        Datacenter (per IP):    $1.20/IP/month (unlimited BW)
        Datacenter (per GB):    $0.59/GB
        Residential:            $6.00/GB (Starter)
        ISP:                    $1.20/IP/month
        Dedicated Datacenter:   $2.25/IP/month
"""

from scrapy import signals
from scrapy.http import Response


# ── Pricing tables (USD) ────────────────────────────────────────────────

PRICING = {
    "webshare": {
        "datacenter": {
            "model": "per_ip_monthly",  # flat fee, unlimited bandwidth
            "per_ip_monthly": 0.03,     # ~$0.03/proxy/month
            "per_gb": 0.0,              # unlimited
        },
        "static_residential": {
            "model": "per_ip_monthly",
            "per_ip_monthly": 0.30,
            "per_gb": 0.0,
        },
        "residential": {
            "model": "per_gb",
            "per_ip_monthly": 0.0,
            "per_gb": 3.50,             # $3.50/GB typical
        },
        "default": {
            "model": "per_gb",
            "per_ip_monthly": 0.0,
            "per_gb": 3.50,
        },
    },
    "oxylabs": {
        "datacenter": {
            "model": "per_ip_monthly",
            "per_ip_monthly": 1.20,
            "per_gb": 0.59,
        },
        "residential": {
            "model": "per_gb",
            "per_ip_monthly": 0.0,
            "per_gb": 6.00,             # Starter plan
        },
        "isp": {
            "model": "per_ip_monthly",
            "per_ip_monthly": 1.20,
            "per_gb": 0.0,
        },
        "dedicated_datacenter": {
            "model": "per_ip_monthly",
            "per_ip_monthly": 2.25,
            "per_gb": 0.0,
        },
        "default": {
            "model": "per_gb",
            "per_ip_monthly": 0.0,
            "per_gb": 6.00,
        },
    },
    "static": {
        "default": {
            "model": "per_ip_monthly",
            "per_ip_monthly": 0.0,      # user-provided, no cost tracking
            "per_gb": 0.0,
        },
    },
}


class ProxyCostCalculatorMiddleware:
    """
    Spider middleware that tracks proxy usage and calculates cost.

    Add to SPIDER_MIDDLEWARES in settings.py:

        SPIDER_MIDDLEWARES = {
            "core.cost_calculator.ProxyCostCalculatorMiddleware": 500,
        }

    Configure pricing in settings.py (optional overrides):

        PROXY_COST_DATACENTER_PER_IP = 1.20   # $/IP/month
        PROXY_COST_RESIDENTIAL_PER_GB = 6.00  # $/GB
        PROXY_COST_MODEL = "per_gb"            # per_gb | per_ip_monthly | per_request
        PROXY_COST_PER_REQUEST = 0.001         # $/request (if per_request model)
    """

    def __init__(self, stats):
        self.stats = stats
        self._total_bytes = 0
        self._total_requests = 0
        self._provider = "none"
        self._proxy_type = "default"

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls(stats=crawler.stats)
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(mw.response_received, signal=signals.response_received)
        return mw

    def spider_opened(self, spider):
        # Detect provider from spider class vars or settings
        self._provider = getattr(
            spider,
            "proxy_provider",
            spider.settings.get("PROXY_PROVIDER", "none"),
        )
        self._proxy_type = getattr(
            spider,
            "proxy_type",
            spider.settings.get("PROXY_TYPE", "default"),
        )

    def response_received(self, response: Response, spider):
        """Track bandwidth per response."""
        self._total_requests += 1

        # Calculate response body size
        body_size = len(response.body) if response.body else 0
        self._total_bytes += body_size

        # Store in stats for per-response tracking
        self.stats.inc_value("proxy/response_count")
        self.stats.inc_value("proxy/bytes_total", body_size)

    def spider_closed(self, spider, reason):
        """Calculate and display cost stats on spider closure."""
        if self._provider == "none":
            return

        # ── Calculate bandwidth ────────────────────────────────────────
        total_bytes = self._total_bytes
        total_mb = total_bytes / (1024 * 1024)
        total_gb = total_mb / 1024

        # ── Get pricing for this provider/type ─────────────────────────
        provider_pricing = PRICING.get(self._provider, PRICING["static"])
        pricing = provider_pricing.get(self._proxy_type, provider_pricing.get("default", {}))

        model = pricing.get("model", "per_gb")
        per_ip_monthly = pricing.get("per_ip_monthly", 0.0)
        per_gb = pricing.get("per_gb", 0.0)

        # ── Calculate cost ─────────────────────────────────────────────
        cost = 0.0

        if model == "per_gb":
            cost = total_gb * per_gb
        elif model == "per_ip_monthly":
            # Estimate number of unique proxies used
            unique_proxies = self.stats.get_value("proxy/unique_proxies", 1)
            cost = unique_proxies * per_ip_monthly
        elif model == "per_request":
            cost = self._total_requests * spider.settings.getfloat("PROXY_COST_PER_REQUEST", 0.001)

        # ── Allow custom pricing from settings ─────────────────────────
        custom_per_gb = spider.settings.getfloat("PROXY_COST_RESIDENTIAL_PER_GB", None)
        custom_per_ip = spider.settings.getfloat("PROXY_COST_DATACENTER_PER_IP", None)
        custom_model = spider.settings.get("PROXY_COST_MODEL", None)

        if custom_model:
            model = custom_model
        if custom_per_gb is not None:
            per_gb = custom_per_gb
        if custom_per_ip is not None:
            per_ip_monthly = custom_per_ip

        # Recalculate with custom pricing
        if model == "per_gb":
            cost = total_gb * per_gb
        elif model == "per_ip_monthly":
            unique_proxies = self.stats.get_value("proxy/unique_proxies", 1)
            cost = unique_proxies * per_ip_monthly
        elif model == "per_request":
            cost = self._total_requests * spider.settings.getfloat("PROXY_COST_PER_REQUEST", 0.001)

        # ── Derived metrics ────────────────────────────────────────────
        cost_per_request = cost / self._total_requests if self._total_requests > 0 else 0
        cost_per_mb = cost / total_mb if total_mb > 0 else 0

        # ── Set stats ──────────────────────────────────────────────────
        self.stats.set_value("proxy/provider", self._provider)
        self.stats.set_value("proxy/type", self._proxy_type)
        self.stats.set_value("proxy/requests", self._total_requests)
        self.stats.set_value("proxy/bandwidth_bytes", total_bytes)
        self.stats.set_value("proxy/bandwidth_mb", round(total_mb, 2))
        self.stats.set_value("proxy/bandwidth_gb", round(total_gb, 4))
        self.stats.set_value("proxy/cost_estimate", round(cost, 4))
        self.stats.set_value("proxy/cost_per_request", round(cost_per_request, 6))
        self.stats.set_value("proxy/cost_per_mb", round(cost_per_mb, 4))
        self.stats.set_value("proxy/pricing_model", model)
        self.stats.set_value("proxy/rate_per_gb", per_gb)
        self.stats.set_value("proxy/rate_per_ip", per_ip_monthly)

        # ── Log summary ────────────────────────────────────────────────
        spider.logger.info(
            "═══ PROXY COST SUMMARY ═══\n"
            "  Provider:        %s\n"
            "  Type:            %s\n"
            "  Requests:        %d\n"
            "  Bandwidth:       %.2f MB (%.4f GB)\n"
            "  Pricing model:   %s\n"
            "  Rate:            $%.2f/GB | $%.2f/IP/mo\n"
            "  ─────────────────────────\n"
            "  ESTIMATED COST:  $%.4f\n"
            "  Cost/request:    $%.6f\n"
            "  Cost/MB:         $%.4f\n"
            "═══════════════════════════",
            self._provider,
            self._proxy_type,
            self._total_requests,
            total_mb,
            total_gb,
            model,
            per_gb,
            per_ip_monthly,
            cost,
            cost_per_request,
            cost_per_mb,
        )
