"""
Atlanta Real Estate Scraper — Zillow Property Data

Scrapes Zillow for Atlanta area properties with proxy support.
Targets highest-traffic zip codes identified from Reddit research:
  30318, 30310, 30349, 30317, 30306, 30307, 30308, 30309, 30312, 30313, 30314, 30316, 30319, 30324, 30326, 30327, 30329, 30332, 30338, 30340, 30341, 30342, 30345, 30346, 30350

Usage:
    # Basic (uses default proxy session):
    scrapy crawl atlanta_zillow

    # With proxy session:
    scrapy crawl atlanta_zillow -a session=premium

    # Override location:
    scrapy crawl atlanta_zillow -a location=US

    # No proxy (direct connection):
    scrapy crawl atlanta_zillow -a proxy=false

Output:
    - JSON file with property data
    - Proxy cost summary in spider_closed stats
"""

import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urlencode, quote


class AtlantaZillowSpider(scrapy.Spider):
    name = "atlanta_zillow"
    allowed_domains = ["zillow.com"]

    # ── Proxy Configuration ─────────────────────────────────────────────
    # Set proxy_provider = "none" to disable proxies for this spider
    proxy_provider = "webshare"  # "webshare" | "oxylabs" | "none"
    proxy_session = "default"
    proxy_rotation = "round-robin"
    proxy_location = "US"
    proxy_type = "datacenter"

    # ── Spider Settings ─────────────────────────────────────────────────
    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "CONCURRENT_REQUESTS": 4,
    }

    # Atlanta zip codes (highest Reddit activity)
    ATLANTA_ZIPS = [
        "30318", "30310", "30349", "30317",  # Top tier
        "30306", "30307", "30308", "30309",  # Midtown/Buckhead
        "30312", "30313", "30314", "30316",  # South/West
        "30319", "30324", "30326", "30327",  # North
        "30329", "30332", "30338", "30340",  # Outer areas
        "30341", "30342", "30345", "30346",  # Decatur/Brookhaven
        "30350",  # Alpharetta
    ]

    def __init__(self, zip_codes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if zip_codes:
            self.zips = zip_codes.split(",")
        else:
            self.zips = self.ATLANTA_ZIPS
        self.results = []

    def start_requests(self):
        """Generate initial requests for each zip code."""
        for zip_code in self.zips:
            # Zillow search URL
            url = f"https://www.zillow.com/homes/{zip_code}_rb/"
            yield scrapy.Request(
                url=url,
                callback=self.parse_search,
                meta={"zip_code": zip_code},
                dont_filter=True,
            )

    def parse_search(self, response):
        """Parse search results page."""
        zip_code = response.meta["zip_code"]
        self.logger.info(f"Parsing zip {zip_code}: {response.url}")

        # Try to extract property links from search results
        # Zillow uses React/Next.js, so we need to find the data
        try:
            # Look for property data in script tags (Next.js data)
            script_data = response.css('script#__NEXT_DATA__::text').get()
            if script_data:
                data = json.loads(script_data)
                # Navigate to property list
                search_results = data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                properties = search_results.get("listResults", [])

                for prop in properties:
                    yield self.extract_property(prop, zip_code)

                # Check for pagination
                next_cursor = search_results.get("nextCursor")
                if next_cursor:
                    yield scrapy.Request(
                        url=f"https://www.zillow.com/homes/{zip_code}_rb/?page={next_cursor}",
                        callback=self.parse_search,
                        meta={"zip_code": zip_code},
                    )
            else:
                # Fallback: parse from HTML
                yield from self.parse_html_search(response, zip_code)

        except json.JSONDecodeError:
            self.logger.warning(f"Failed to parse JSON for zip {zip_code}")
            yield from self.parse_html_search(response, zip_code)

    def parse_html_search(self, response, zip_code):
        """Fallback: parse property data from HTML elements."""
        # Extract property cards
        property_cards = response.css('article[data-test="property-card"]')

        for card in property_cards:
            try:
                link = card.css('a::attr(href)').get()
                address = card.css('address::text').get()
                price = card.css('[data-test="property-card-price"]::text').get()
                beds = card.css('[data-test="bed"]::text').get()
                baths = card.css('[data-test="bath"]::text').get()
                sqft = card.css('[data-test="sqft"]::text').get()

                yield {
                    "zip_code": zip_code,
                    "url": response.urljoin(link) if link else None,
                    "address": address.strip() if address else None,
                    "price": self.clean_price(price),
                    "beds": self.clean_number(beds),
                    "baths": self.clean_number(baths),
                    "sqft": self.clean_number(sqft),
                    "scraped_at": datetime.now().isoformat(),
                }
            except Exception as e:
                self.logger.warning(f"Error parsing card: {e}")

    def extract_property(self, prop, zip_code):
        """Extract property data from Zillow JSON response."""
        return {
            "zip_code": zip_code,
            "zpid": prop.get("id"),
            "url": f"https://www.zillow.com{prop.get('detailUrl', '')}",
            "address": prop.get("address"),
            "city": prop.get("addressCity"),
            "state": prop.get("addressState"),
            "zip": prop.get("addressZipcode"),
            "price": prop.get("unformattedPrice"),
            "price_display": prop.get("price"),
            "beds": prop.get("beds"),
            "baths": prop.get("baths"),
            "sqft": prop.get("area"),
            "lot_size": prop.get("lotAreaValue"),
            "property_type": prop.get("homeType"),
            "year_built": prop.get("yearBuilt"),
            "latitude": prop.get("latitude"),
            "longitude": prop.get("longitude"),
            "status": prop.get("homeStatus"),
            "days_on_zillow": prop.get("daysOnZillow"),
            "scraped_at": datetime.now().isoformat(),
        }

    def clean_price(self, price_str):
        """Clean price string to number."""
        if not price_str:
            return None
        cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    def clean_number(self, num_str):
        """Clean number string."""
        if not num_str:
            return None
        cleaned = re.sub(r'[^\d.]', '', num_str)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    def closed(self, reason):
        """Called when spider closes."""
        self.logger.info(f"Spider closed: {reason}. Total items: {len(self.results)}")
