"""
Atlanta Real Estate Scraper — Redfin Market Data

Scrapes Redfin for Atlanta area properties and market statistics.
Redfin provides more detailed market data than Zillow.

Usage:
    # Basic:
    scrapy crawl atlanta_redfin

    # With proxy session:
    scrapy crawl atlanta_redfin -a session=premium

    # Specific zip codes:
    scrapy crawl atlanta_redfin -a zip_codes=30318,30310,30349

Output:
    - JSON file with property and market data
    - Proxy cost summary in spider_closed stats
"""

import scrapy
import json
import re
from datetime import datetime
from urllib.parse import quote


class AtlantaRedfinSpider(scrapy.Spider):
    name = "atlanta_redfin"
    allowed_domains = ["redfin.com"]

    # ── Proxy Configuration ─────────────────────────────────────────────
    proxy_provider = "webshare"
    proxy_session = "default"
    proxy_rotation = "round-robin"
    proxy_location = "US"
    proxy_type = "datacenter"

    # ── Spider Settings ─────────────────────────────────────────────────
    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "CONCURRENT_REQUESTS": 4,
    }

    # Atlanta zip codes
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

    def start_requests(self):
        """Generate initial requests for each zip code."""
        for zip_code in self.zips:
            # Redfin search URL
            url = f"https://www.redfin.com/zipcode/{zip_code}/filter/include=sold-3mo"
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

        # Redfin stores data in a script tag
        script_data = response.css('script[data-rf Initialization="true"]::text').get()

        if script_data:
            try:
                # Extract JSON from script
                json_match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', script_data)
                if json_match:
                    data = json.loads(json_match.group(1))
                    # Navigate to property list
                    search_results = data.get("searchResults", {})
                    properties = search_results.get("results", [])

                    for prop in properties:
                        yield self.extract_property(prop, zip_code)
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON for zip {zip_code}")

        # Fallback: parse from HTML
        yield from self.parse_html_search(response, zip_code)

    def parse_html_search(self, response, zip_code):
        """Parse property data from HTML elements."""
        # Extract property cards
        property_cards = response.css('.HomeCardContainer')

        for card in property_cards:
            try:
                link = card.css('a::attr(href)').get()
                price = card.css('.homecardV2Price::text').get()
                beds = card.css('.HomeStatsV2 .raCard::text').getall()
                address_parts = card.css('.homeAddressV2 .homeAddress::text').getall()

                yield {
                    "zip_code": zip_code,
                    "url": response.urljoin(link) if link else None,
                    "address": " ".join(address_parts) if address_parts else None,
                    "price": self.clean_price(price),
                    "beds": self.clean_number(beds[0]) if beds else None,
                    "baths": self.clean_number(beds[1]) if len(beds) > 1 else None,
                    "sqft": self.clean_number(beds[2]) if len(beds) > 2 else None,
                    "scraped_at": datetime.now().isoformat(),
                }
            except Exception as e:
                self.logger.warning(f"Error parsing card: {e}")

    def extract_property(self, prop, zip_code):
        """Extract property data from Redfin JSON response."""
        return {
            "zip_code": zip_code,
            "redfin_id": prop.get("id"),
            "url": prop.get("url"),
            "address": prop.get("address"),
            "city": prop.get("city"),
            "state": prop.get("stateOrProvince"),
            "zip": prop.get("zipCode"),
            "price": prop.get("price"),
            "beds": prop.get("beds"),
            "baths": prop.get("baths"),
            "sqft": prop.get("sqft"),
            "lot_size": prop.get("lotSize"),
            "property_type": prop.get("propertyType"),
            "year_built": prop.get("yearBuilt"),
            "latitude": prop.get("latitude"),
            "longitude": prop.get("longitude"),
            "status": prop.get("status"),
            "days_on_market": prop.get("dom"),
            "price_per_sqft": prop.get("pricePerSqFt"),
            "hoa_fee": prop.get("hoaFee"),
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
        self.logger.info(f"Spider closed: {reason}")
