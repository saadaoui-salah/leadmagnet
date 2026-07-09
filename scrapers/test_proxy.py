"""
Quick test script to verify proxy setup.

Usage:
    python test_proxy.py
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from core.cost_calculator import ProxyCostCalculatorMiddleware
        print("✓ ProxyCostCalculatorMiddleware")
    except ImportError as e:
        print(f"✗ ProxyCostCalculatorMiddleware: {e}")
        return False

    try:
        from core.proxy_manager import ProxyManager
        print("✓ ProxyManager")
    except ImportError as e:
        print(f"✗ ProxyManager: {e}")
        return False

    try:
        from core.spiders.proxy_example import ProxyExampleSpider
        print("✓ ProxyExampleSpider")
    except ImportError as e:
        print(f"✗ ProxyExampleSpider: {e}")
        return False

    try:
        from core.spiders.atlanta_zillow import AtlantaZillowSpider
        print("✓ AtlantaZillowSpider")
    except ImportError as e:
        print(f"✗ AtlantaZillowSpider: {e}")
        return False

    try:
        from core.spiders.atlanta_redfin import AtlantaRedfinSpider
        print("✓ AtlantaRedfinSpider")
    except ImportError as e:
        print(f"✗ AtlantaRedfinSpider: {e}")
        return False

    try:
        from core.spiders.biggerpockets_leads import BiggerPocketsLeadsSpider
        print("✓ BiggerPocketsLeadsSpider")
    except ImportError as e:
        print(f"✗ BiggerPocketsLeadsSpider: {e}")
        return False

    return True


def test_env_vars():
    """Test environment variables."""
    print("\nTesting environment variables...")

    webshare_token = os.getenv("WEBSHARE_API_TOKEN")
    if webshare_token:
        print(f"✓ WEBSHARE_API_TOKEN: {webshare_token[:10]}...")
    else:
        print("✗ WEBSHARE_API_TOKEN: Not set")

    oxylabs_user = os.getenv("OXYLABS_USERNAME")
    if oxylabs_user:
        print(f"✓ OXYLABS_USERNAME: {oxylabs_user}")
    else:
        print("✗ OXYLABS_USERNAME: Not set")

    oxylabs_pass = os.getenv("OXYLABS_PASSWORD")
    if oxylabs_pass:
        print(f"✓ OXYLABS_PASSWORD: {'*' * len(oxylabs_pass)}")
    else:
        print("✗ OXYLABS_PASSWORD: Not set")


def test_settings():
    """Test Scrapy settings."""
    print("\nTesting Scrapy settings...")

    try:
        import scrapy
        from scrapy.utils.project import get_project_settings

        settings = get_project_settings()

        proxy_enabled = settings.getbool("PROXY_ENABLED", False)
        print(f"{'✓' if proxy_enabled else '✗'} PROXY_ENABLED: {proxy_enabled}")

        proxy_provider = settings.get("PROXY_PROVIDER", "none")
        print(f"✓ PROXY_PROVIDER: {proxy_provider}")

        proxy_type = settings.get("PROXY_TYPE", "none")
        print(f"✓ PROXY_TYPE: {proxy_type}")

        # Check cost calculator middleware
        spider_middlewares = settings.getdict("SPIDER_MIDDLEWARES", {})
        if "core.cost_calculator.ProxyCostCalculatorMiddleware" in spider_middlewares:
            print("✓ ProxyCostCalculatorMiddleware: Enabled")
        else:
            print("✗ ProxyCostCalculatorMiddleware: Not in SPIDER_MIDDLEWARES")

    except Exception as e:
        print(f"✗ Error loading settings: {e}")


def test_spiders():
    """Test spider configurations."""
    print("\nTesting spider configurations...")

    try:
        from core.spiders.atlanta_zillow import AtlantaZillowSpider

        spider = AtlantaZillowSpider()
        print(f"✓ AtlantaZillowSpider")
        print(f"  - provider: {spider.proxy_provider}")
        print(f"  - session: {spider.proxy_session}")
        print(f"  - rotation: {spider.proxy_rotation}")
        print(f"  - location: {spider.proxy_location}")
        print(f"  - type: {spider.proxy_type}")
        print(f"  - zips: {len(spider.zips)} zip codes")

    except Exception as e:
        print(f"✗ Error testing AtlantaZillowSpider: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Proxy System Test")
    print("=" * 60)

    if not test_imports():
        print("\n✗ Import test failed")
        return

    test_env_vars()
    test_settings()
    test_spiders()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set WEBSHARE_API_TOKEN in .env")
    print("2. Run: scrapy crawl proxy_example")
    print("3. Run: scrapy crawl atlanta_zillow")


if __name__ == "__main__":
    main()
