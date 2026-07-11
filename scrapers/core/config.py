"""
Reusable config accessor — reads from spider.custom_settings, then env vars, then default.

Usage:
    from core.config import get_config

    # In spider or middleware:
    api_token = get_config(spider, "WEBSHARE_API_TOKEN", "")
    port = get_config(spider, "OXYLABS_PORT", 8000, cast=int)
"""

import os
from typing import Any, Optional, Type


def get_config(
    spider,
    key: str,
    default: Any = None,
    cast: Optional[Type] = None,
) -> Any:
    """
    Get config value from spider.custom_settings → env vars → default.

    Priority:
        1. spider.custom_settings[key]
        2. os.getenv(key)
        3. default

    Args:
        spider: Scrapy spider instance
        key: Config key name (e.g. "WEBSHARE_API_TOKEN")
        default: Fallback value if not found
        cast: Optional type cast (e.g. int, str, bool)

    Returns:
        Config value or default

    Example:
        token = get_config(spider, "WEBSHARE_API_TOKEN", "")
        port = get_config(spider, "OXYLABS_PORT", 8000, cast=int)
        enabled = get_config(spider, "PROXY_ENABLED", False, cast=bool)
    """
    value = None

    # 1. Check spider.custom_settings
    custom_settings = getattr(spider, "custom_settings", None)
    if custom_settings and key in custom_settings:
        value = custom_settings[key]

    # 2. Check env vars
    if value is None:
        value = os.getenv(key)

    # 3. Use default
    if value is None:
        return default

    # Cast to type if specified
    if cast is not None:
        try:
            if cast == bool:
                return str(value).lower() in ("true", "1", "yes")
            return cast(value)
        except (ValueError, TypeError):
            return default

    return value
