"""
Multi-Provider Proxy Manager — supports Webshare and Oxylabs with rotation.

Class Variables (set in settings.py or spider):
    PROXY_PROVIDER       — "webshare" | "oxylabs" | "static"
    PROXY_SESSIONS       — dict of named sessions with their own proxy pools
    PROXY_ROTATION       — rotation strategy: "round-robin", "random", "least-used"
    PROXY_LOCATION       — country filter (ISO codes), e.g. "US" or "US,GB" or "ZZ"
    PROXY_STATIC_LIST    — list of proxy URLs for "static" provider
                           e.g. ["http://user:pass@host:port", ...]

Oxylabs curl format:
    curl -x dc.oxylabs.io:8000 -U "user-reaalestate_qNES0-country-US:G9R46D3kqnW=p3" https://ip.oxylabs.io/location

    The middleware parses this into:
        proxy_address = dc.oxylabs.io
        port = 8000
        username = user-reaalestate_qNES0-country-US
        password = G9R46D3kqnW=p3
        url = http://user-reaalestate_qNES0-country-US:G9R46D3kqnW=p3@dc.oxylabs.io:8000
"""

import os
import json
import time
import random
import threading
from pathlib import Path
from itertools import cycle
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests


@dataclass
class ProxyEntry:
    """Single proxy with metadata."""
    id: str
    username: str
    password: str
    proxy_address: str
    port: int
    country_code: str = ""
    city_name: str = ""
    provider: str = ""
    valid: bool = True
    use_count: int = 0
    last_used: float = 0.0

    @property
    def url(self) -> str:
        return f"http://{self.username}:{self.password}@{self.proxy_address}:{self.port}"

    @property
    def as_dict(self) -> dict:
        return {
            "http": self.url,
            "https": self.url,
        }


class ProxyProvider:
    """Base class for proxy providers."""

    def fetch_proxies(self, session_cfg: dict) -> list[ProxyEntry]:
        raise NotImplementedError


class WebshareProvider(ProxyProvider):
    """Fetch proxies from Webshare API."""

    BASE_URL = "https://proxy.webshare.io/api/v2"

    # Webshare plan IDs for different proxy types
    PLAN_IDS = {
        "datacenter": 13766293,  # your datacenter plan
        "static_residential": 13768706,  # your static residential plan
        "residential": None,  # rotating residential
    }

    def __init__(self, api_token: str, plan_id: Optional[int] = None):
        self.api_token = api_token
        self.plan_id = plan_id

    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self.api_token}",
            "X-Webshare-Source": "WebshareSkill/1.0 (LLM; ScrapyMiddleware)",
        }

    def fetch_proxies(self, session_cfg: dict) -> list[ProxyEntry]:
        mode = session_cfg.get("mode", "direct")
        country = session_cfg.get("country", "ZZ")
        page_size = session_cfg.get("page_size", 100)
        proxy_type = session_cfg.get("proxy_type", "datacenter")

        # Determine plan ID
        plan_id = self.plan_id
        if not plan_id:
            plan_id = session_cfg.get("plan_id")
        if not plan_id:
            plan_id = self.PLAN_IDS.get(proxy_type)

        all_proxies = []
        page = 1

        params = {"mode": mode, "page_size": page_size}
        if plan_id:
            params["plan_id"] = plan_id
        if country and country.upper() != "ZZ":
            params["country_code__in"] = country.upper()

        while True:
            params["page"] = page
            resp = requests.get(
                f"{self.BASE_URL}/proxy/list/",
                headers=self._headers(),
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            all_proxies.extend(results)

            if not data.get("next") or not results:
                break
            page += 1

        return [
            ProxyEntry(
                id=str(p["id"]),
                username=p["username"],
                password=p["password"],
                proxy_address=p["proxy_address"],
                port=p["port"],
                country_code=p.get("country_code", ""),
                city_name=p.get("city_name", ""),
                provider="webshare",
                valid=p.get("valid", True),
            )
            for p in all_proxies
            if p.get("valid", True)
        ]


class OxylabsProvider(ProxyProvider):
    """
    Oxylabs proxy provider.

    Supports two config formats:

    1. Explicit host/user/pass in session config:
        PROXY_SESSIONS = {
            "default": {
                "provider": "oxylabs",
                "host": "dc.oxylabs.io",
                "port": 8000,
                "username": "user-reaalestate_qNES0-country-US",
                "password": "G9R46D3kqnW=p3",
                "strategy": "round-robin",
            }
        }

    2. Curl-style proxy string:
        PROXY_SESSIONS = {
            "default": {
                "provider": "oxylabs",
                "proxy_url": "http://user:pass@dc.oxylabs.io:8000",
                "strategy": "round-robin",
            }
        }

    3. Multiple proxies (pool):
        PROXY_SESSIONS = {
            "default": {
                "provider": "oxylabs",
                "proxies": [
                    "http://user-country-US:pass@dc.oxylabs.io:8000",
                    "http://user-country-GB:pass@dc.oxylabs.io:8000",
                ],
                "strategy": "random",
            }
        }

    4. Credentials from settings (.env):
        OXYLABS_HOST=dc.oxylabs.io
        OXYLABS_PORT=8000
        OXYLABS_USERNAME=user-reaalestate_qNES0-country-US
        OXYLABS_PASSWORD=G9R46D3kqnW=p3
    """

    def __init__(
        self,
        host: str = "dc.oxylabs.io",
        port: int = 8000,
        username: str = "",
        password: str = "",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @staticmethod
    def parse_proxy_url(url: str) -> ProxyEntry:
        """Parse a proxy URL into a ProxyEntry."""
        if not url.startswith("http"):
            url = f"http://{url}"

        parsed = urlparse(url)
        username = parsed.username or ""
        password = parsed.password or ""
        hostname = parsed.hostname or ""
        port = parsed.port or 8000

        # Try to extract country from username (Oxylabs convention: user-country-XX)
        country_code = ""
        if "-country-" in username:
            parts = username.split("-country-")
            if len(parts) > 1:
                country_code = parts[-1].upper()

        return ProxyEntry(
            id=f"oxylabs-{hostname}:{port}-{country_code}",
            username=username,
            password=password,
            proxy_address=hostname,
            port=port,
            country_code=country_code,
            provider="oxylabs",
        )

    def fetch_proxies(self, session_cfg: dict) -> list[ProxyEntry]:
        proxies = []

        # Option 1: Multiple proxies list
        if "proxies" in session_cfg:
            for i, proxy_url in enumerate(session_cfg["proxies"]):
                entry = self.parse_proxy_url(proxy_url)
                entry.id = f"oxylabs-{i}-{entry.proxy_address}:{entry.port}"
                proxies.append(entry)
            return proxies

        # Option 2: Single proxy_url
        if "proxy_url" in session_cfg:
            return [self.parse_proxy_url(session_cfg["proxy_url"])]

        # Option 3: Explicit host/user/pass (or use constructor defaults)
        host = session_cfg.get("host", self.host)
        port = session_cfg.get("port", self.port)
        username = session_cfg.get("username", self.username)
        password = session_cfg.get("password", self.password)

        country_code = ""
        if "-country-" in username:
            parts = username.split("-country-")
            if len(parts) > 1:
                country_code = parts[-1].upper()

        return [
            ProxyEntry(
                id=f"oxylabs-{host}:{port}",
                username=username,
                password=password,
                proxy_address=host,
                port=port,
                country_code=country_code,
                provider="oxylabs",
            )
        ]


class StaticProvider(ProxyProvider):
    """
    Static proxy list — for manually provided proxies.

    PROXY_SESSIONS = {
        "default": {
            "provider": "static",
            "proxies": [
                "http://user:pass@host1:port",
                "http://user:pass@host2:port",
            ],
            "strategy": "round-robin",
        }
    }
    """

    def fetch_proxies(self, session_cfg: dict) -> list[ProxyEntry]:
        proxy_urls = session_cfg.get("proxies", [])
        return [
            OxylabsProvider.parse_proxy_url(url)  # Same parsing logic
            for url in proxy_urls
        ]


# ── Provider factory ─────────────────────────────────────────────────────

PROVIDERS = {
    "webshare": WebshareProvider,
    "oxylabs": OxylabsProvider,
    "static": StaticProvider,
}


def get_provider(name: str, **kwargs) -> ProxyProvider:
    """Create a provider instance by name."""
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown proxy provider: {name}. Choose from: {list(PROVIDERS.keys())}")
    return cls(**kwargs)


# ── Main Manager ─────────────────────────────────────────────────────────

class ProxyManager:
    """
    Multi-provider proxy manager with rotation and caching.

    Usage in spider:
        proxy_mgr = ProxyManager.from_settings(spider.settings)
        proxy = proxy_mgr.get_proxy(session="default")
    """

    CACHE_DIR = Path(__file__).parent.parent / ".proxy_cache"
    CACHE_FILE = CACHE_DIR / "proxies.json"

    DEFAULT_SESSIONS = {
        "default": {
            "provider": "webshare",
            "strategy": "round-robin",
            "country": "US",
            "mode": "direct",
        }
    }
    DEFAULT_ROTATION = "round-robin"
    DEFAULT_LOCATION = "US"
    DEFAULT_REFRESH_INTERVAL = 300

    def __init__(
        self,
        sessions: Optional[dict] = None,
        rotation: str = "round-robin",
        location: str = "US",
        refresh_interval: int = 300,
    ):
        self.sessions = sessions or self.DEFAULT_SESSIONS.copy()
        self.default_rotation = rotation
        self.default_location = location
        self.refresh_interval = refresh_interval

        self._providers: dict[str, ProxyProvider] = {}
        self._proxies: dict[str, list[ProxyEntry]] = {}
        self._iterators: dict[str, cycle] = {}
        self._sticky_proxy: dict[str, str] = {}  # session -> proxy_id for on-block strategy
        self._lock = threading.Lock()
        self._last_refresh: float = 0
        self._cached_session_cfg: dict = {}

        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._init_providers()

    def _init_providers(self):
        """Initialize provider instances for each session."""
        for session_name, cfg in self.sessions.items():
            provider_name = cfg.get("provider", "webshare")

            kwargs = {}
            if provider_name == "webshare":
                token = cfg.get("api_token") or os.getenv("WEBSHARE_API_TOKEN", "")
                if not token:
                    raise ValueError(
                        f"Session '{session_name}' needs WEBSHARE_API_TOKEN. "
                        "Set it in session config or .env"
                    )
                kwargs["api_token"] = token
                # Plan ID can come from session config or proxy_type
                plan_id = cfg.get("plan_id")
                if not plan_id:
                    proxy_type = cfg.get("proxy_type", "datacenter")
                    plan_id = WebshareProvider.PLAN_IDS.get(proxy_type)
                kwargs["plan_id"] = plan_id
            elif provider_name == "oxylabs":
                # Oxylabs credentials come from session config or settings
                kwargs["host"] = cfg.get("host") or os.getenv("OXYLABS_HOST", "dc.oxylabs.io")
                kwargs["port"] = cfg.get("port") or int(os.getenv("OXYLABS_PORT", "8000"))
                kwargs["username"] = cfg.get("username") or os.getenv("OXYLABS_USERNAME", "")
                kwargs["password"] = cfg.get("password") or os.getenv("OXYLABS_PASSWORD", "")

            self._providers[session_name] = get_provider(provider_name, **kwargs)

    @classmethod
    def from_settings(cls, settings) -> "ProxyManager":
        """Build manager from Scrapy settings object."""
        sessions = settings.getdict("PROXY_SESSIONS", None)

        # If no sessions defined, build from top-level settings
        if not sessions:
            provider = settings.get("PROXY_PROVIDER", "webshare")
            proxy_type = settings.get("PROXY_TYPE", "datacenter")

            # Map proxy_type to Webshare mode
            mode = settings.get("PROXY_MODE", "direct")
            if proxy_type == "backbone":
                mode = "backbone"

            sessions = {
                "default": {
                    "provider": provider,
                    "strategy": settings.get("PROXY_ROTATION", cls.DEFAULT_ROTATION),
                    "country": settings.get("PROXY_LOCATION", cls.DEFAULT_LOCATION),
                    "mode": mode,
                    "proxy_type": proxy_type,
                }
            }

            # Add provider-specific config
            if provider == "webshare":
                sessions["default"]["api_token"] = os.getenv("WEBSHARE_API_TOKEN", "")
                plan_id = settings.getint("PROXY_PLAN_ID", None)
                if plan_id:
                    sessions["default"]["plan_id"] = plan_id
            elif provider == "oxylabs":
                sessions["default"]["host"] = settings.get("OXYLABS_HOST", "dc.oxylabs.io")
                sessions["default"]["port"] = settings.getint("OXYLABS_PORT", 8000)
                sessions["default"]["username"] = settings.get("OXYLABS_USERNAME", "")
                sessions["default"]["password"] = settings.get("OXYLABS_PASSWORD", "")

        rotation = settings.get("PROXY_ROTATION", cls.DEFAULT_ROTATION)
        location = settings.get("PROXY_LOCATION", cls.DEFAULT_LOCATION)
        refresh_interval = settings.getint("PROXY_REFRESH_INTERVAL", cls.DEFAULT_REFRESH_INTERVAL)

        return cls(
            sessions=sessions,
            rotation=rotation,
            location=location,
            refresh_interval=refresh_interval,
        )

    @classmethod
    def from_spider(cls, spider) -> "ProxyManager":
        """Build manager from spider class variables and settings.
        
        Spider class variables override settings:
            proxy_provider = "webshare"  # "webshare" | "oxylabs" | "none"
            proxy_session = "default"
            proxy_rotation = "round-robin"
            proxy_location = "US"
            proxy_type = "datacenter"
        """
        settings = spider.settings

        # Get config from spider class vars first, then fallback to settings
        provider = getattr(spider, "proxy_provider", None) or settings.get("PROXY_PROVIDER", "webshare")
        
        # If provider is "none", return None (no proxy)
        if provider == "none":
            return None

        proxy_type = getattr(spider, "proxy_type", None) or settings.get("PROXY_TYPE", "datacenter")
        rotation = getattr(spider, "proxy_rotation", None) or settings.get("PROXY_ROTATION", cls.DEFAULT_ROTATION)
        location = getattr(spider, "proxy_location", None) or settings.get("PROXY_LOCATION", cls.DEFAULT_LOCATION)
        session = getattr(spider, "proxy_session", "default")

        # Map proxy_type to Webshare mode
        mode = getattr(spider, "proxy_mode", None) or settings.get("PROXY_MODE", "direct")
        if proxy_type == "backbone":
            mode = "backbone"

        # Build session config
        sessions = {
            session: {
                "provider": provider,
                "strategy": rotation,
                "country": location,
                "mode": mode,
                "proxy_type": proxy_type,
            }
        }

        # Add provider-specific config from spider.custom_settings or settings
        custom_settings = getattr(spider, "custom_settings", {}) or {}

        if provider == "webshare":
            api_token = custom_settings.get("WEBSHARE_API_TOKEN") or os.getenv("WEBSHARE_API_TOKEN", "")
            sessions[session]["api_token"] = api_token
            plan_id = custom_settings.get("PROXY_PLAN_ID") or settings.getint("PROXY_PLAN_ID", None)
            if plan_id:
                sessions[session]["plan_id"] = plan_id
        elif provider == "oxylabs":
            sessions[session]["host"] = custom_settings.get("OXYLABS_HOST") or settings.get("OXYLABS_HOST", "dc.oxylabs.io")
            sessions[session]["port"] = custom_settings.get("OXYLABS_PORT") or settings.getint("OXYLABS_PORT", 8000)
            sessions[session]["username"] = custom_settings.get("OXYLABS_USERNAME") or settings.get("OXYLABS_USERNAME", "")
            sessions[session]["password"] = custom_settings.get("OXYLABS_PASSWORD") or settings.get("OXYLABS_PASSWORD", "")

        refresh_interval = settings.getint("PROXY_REFRESH_INTERVAL", cls.DEFAULT_REFRESH_INTERVAL)

        return cls(
            sessions=sessions,
            rotation=rotation,
            location=location,
            refresh_interval=refresh_interval,
        )

    # ── Cache ─────────────────────────────────────────────────────────────

    def _save_cache(self):
        cache = {}
        for session, proxies in self._proxies.items():
            cache[session] = [
                {
                    "id": p.id,
                    "username": p.username,
                    "password": p.password,
                    "proxy_address": p.proxy_address,
                    "port": p.port,
                    "country_code": p.country_code,
                    "city_name": p.city_name,
                    "provider": p.provider,
                    "valid": p.valid,
                    "use_count": p.use_count,
                }
                for p in proxies
            ]
        self.CACHE_FILE.write_text(json.dumps(cache, indent=2))

    def _load_cache(self) -> bool:
        if not self.CACHE_FILE.exists():
            return False
        try:
            cache = json.loads(self.CACHE_FILE.read_text())
            for session, items in cache.items():
                self._proxies[session] = [
                    ProxyEntry(
                        id=item["id"],
                        username=item["username"],
                        password=item["password"],
                        proxy_address=item["proxy_address"],
                        port=item["port"],
                        country_code=item.get("country_code", ""),
                        city_name=item.get("city_name", ""),
                        provider=item.get("provider", ""),
                        valid=item.get("valid", True),
                        use_count=item.get("use_count", 0),
                    )
                    for item in items
                ]
                self._build_iterator(session)
            self._last_refresh = time.time()
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    # ── Refresh ───────────────────────────────────────────────────────────

    def refresh(self, force: bool = False):
        """Fetch fresh proxies from provider (respects refresh interval)."""
        now = time.time()

        # Force refresh if country changed
        for session_name, session_cfg in self.sessions.items():
            current_country = session_cfg.get("country", "ZZ")
            cached_cfg = self._cached_session_cfg.get(session_name, {})
            cached_country = cached_cfg.get("country", "ZZ")
            if current_country != cached_country:
                force = True
                break

        if not force and (now - self._last_refresh) < self.refresh_interval:
            return

        with self._lock:
            if not force and (time.time() - self._last_refresh) < self.refresh_interval:
                return

            for session_name, session_cfg in self.sessions.items():
                provider = self._providers.get(session_name)
                if not provider:
                    continue

                try:
                    raw = provider.fetch_proxies(session_cfg)
                    self._proxies[session_name] = raw
                    self._build_iterator(session_name)
                except Exception as e:
                    if not self._load_cache():
                        raise RuntimeError(f"Proxy fetch failed ({session_name}): {e}")

            self._last_refresh = time.time()
            self._cached_session_cfg = {k: v.copy() for k, v in self.sessions.items()}
            self._save_cache()

    def _build_iterator(self, session_name: str):
        """Build a rotation iterator for a session."""
        proxies = self._proxies.get(session_name, [])
        if not proxies:
            return

        strategy = self.sessions.get(session_name, {}).get(
            "strategy", self.default_rotation
        )

        if strategy == "random":
            random.shuffle(proxies)
            self._iterators[session_name] = cycle(proxies)
        elif strategy == "least-used":
            sorted_proxies = sorted(proxies, key=lambda p: p.use_count)
            self._iterators[session_name] = cycle(sorted_proxies)
        elif strategy == "on-block":
            # Sticky strategy: reuse same proxy until blocked
            self._sticky_proxy = {}
        else:  # round-robin
            self._iterators[session_name] = cycle(proxies)

    # ── Get proxy ─────────────────────────────────────────────────────────

    def get_proxy(self, session: str = "default") -> Optional[ProxyEntry]:
        """Get the next proxy for a session."""
        self.refresh()

        with self._lock:
            proxies = self._proxies.get(session, [])
            if not proxies:
                return None

            strategy = self.sessions.get(session, {}).get(
                "strategy", self.default_rotation
            )

            # On-block strategy: reuse same proxy until marked bad
            if strategy == "on-block":
                if session in self._sticky_proxy:
                    proxy_id = self._sticky_proxy[session]
                    for p in proxies:
                        if p.id == proxy_id:
                            p.use_count += 1
                            p.last_used = time.time()
                            return p
                # No sticky proxy yet, pick first one
                proxy = proxies[0]
                self._sticky_proxy[session] = proxy.id
                proxy.use_count += 1
                proxy.last_used = time.time()
                return proxy

            iterator = self._iterators.get(session)
            if iterator is None:
                self._build_iterator(session)
                iterator = self._iterators.get(session)
                if iterator is None:
                    return None

            proxy = next(iterator)
            proxy.use_count += 1
            proxy.last_used = time.time()
            return proxy

    def get_random_proxy(self, session: str = "default") -> Optional[ProxyEntry]:
        """Get a random proxy from a session pool."""
        self.refresh()
        proxies = self._proxies.get(session, [])
        if not proxies:
            return None
        proxy = random.choice(proxies)
        proxy.use_count += 1
        proxy.last_used = time.time()
        return proxy

    def get_proxy_url(self, session: str = "default") -> Optional[str]:
        """Shorthand: get just the proxy URL string."""
        proxy = self.get_proxy(session=session)
        return proxy.url if proxy else None

    def get_all_proxies(self, session: str = "default") -> list[ProxyEntry]:
        """Return all proxies for a session."""
        self.refresh()
        return self._proxies.get(session, [])

    def mark_bad(self, proxy_id: str, session: str = "default"):
        """Mark a proxy as invalid (removed from rotation).
        
        proxy_id can be either:
        - The proxy ID (e.g. "d-17461981689")
        - The address:port (e.g. "184.174.56.234:5246")
        """
        with self._lock:
            proxies = self._proxies.get(session, [])
            
            # Find proxy by ID or by address:port
            removed_id = None
            new_proxies = []
            for p in proxies:
                if p.id == proxy_id or f"{p.proxy_address}:{p.port}" == proxy_id:
                    removed_id = p.id
                    continue
                new_proxies.append(p)
            
            self._proxies[session] = new_proxies

            # Clear sticky proxy if it was the one marked bad
            if session in self._sticky_proxy:
                sticky_id = self._sticky_proxy[session]
                if sticky_id == removed_id or sticky_id == proxy_id:
                    del self._sticky_proxy[session]

            self._build_iterator(session)

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return proxy pool statistics."""
        return {
            session: {
                "total": len(proxies),
                "valid": sum(1 for p in proxies if p.valid),
                "total_uses": sum(p.use_count for p in proxies),
                "providers": list(set(p.provider for p in proxies)),
            }
            for session, proxies in self._proxies.items()
        }


# ── Backward compatibility ───────────────────────────────────────────────
WebshareProxyManager = ProxyManager
