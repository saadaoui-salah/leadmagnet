"""
BiggerPockets Lead Scraper — Atlanta Real Estate Investors

Scrapes BiggerPockets forums for users asking about Atlanta real estate.
These are potential leads for market reports.

Target threads identified from research:
  - "New to Atlanta, best areas to invest?" (Nov 2025)
  - "First Investment 2026" (Feb 2026)
  - "Investing in Atlanta, GA" (Dec 2023)

Usage:
    # Basic:
    scrapy crawl biggerpockets_leads

    # With proxy session:
    scrapy crawl biggerpockets_leads -a session=premium

Output:
    - JSON file with user profiles and questions
    - Potential leads for market report sales
"""

import scrapy
import json
import re
from datetime import datetime


class BiggerPocketsLeadsSpider(scrapy.Spider):
    name = "biggerpockets_leads"
    allowed_domains = ["biggerpockets.com"]

    # ── Proxy Configuration ─────────────────────────────────────────────
    # Set proxy_provider = "none" to disable proxies for this spider
    proxy_provider = "webshare"  # "webshare" | "oxylabs" | "none"
    proxy_session = "default"
    proxy_rotation = "round-robin"
    proxy_location = "US"
    proxy_type = "datacenter"

    # ── Spider Settings ─────────────────────────────────────────────────
    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "CONCURRENT_REQUESTS": 4,
        "ROBOTSTXT_OBEY": False,
    }

    # Target search terms for Atlanta real estate
    SEARCH_TERMS = [
        "Atlanta investment",
        "Atlanta real estate",
        "Atlanta rental property",
        "Atlanta fix and flip",
        "Atlanta buy and hold",
        "Atlanta BRRRR",
        "Atlanta starter rental",
        "Atlanta cash flow",
        "Atlanta property management",
        "Atlanta neighborhoods",
    ]

    # Target forum sections
    FORUM_SECTIONS = [
        "Real Estate Investing",
        "New Member Introduction",
        "Rental Properties",
        "Fixing and Flipping Houses",
        "Real Estate Developer",
    ]

    def start_requests(self):
        """Generate initial requests for search and forum sections."""
        # Search for Atlanta discussions
        for term in self.SEARCH_TERMS:
            url = f"https://www.biggerpockets.com/search?q={term.replace(' ', '+')}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_search,
                meta={"search_term": term},
                dont_filter=True,
            )

        # Also search forum posts directly
        for section in self.FORUM_SECTIONS:
            url = f"https://www.biggerpockets.com/forums/{section.lower().replace(' ', '-')}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_forum,
                meta={"section": section},
                dont_filter=True,
            )

    def parse_search(self, response):
        """Parse search results page."""
        search_term = response.meta["search_term"]
        self.logger.info(f"Parsing search: {search_term}")

        # Extract result links
        result_links = response.css('.search-result a::attr(href)').getall()

        for link in result_links:
            if '/forums/' in link or '/market/' in link:
                yield scrapy.Request(
                    url=response.urljoin(link),
                    callback=self.parse_thread,
                    meta={"search_term": search_term},
                )

        # Check for pagination
        next_page = response.css('.pagination-next::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_search,
                meta={"search_term": search_term},
            )

    def parse_forum(self, response):
        """Parse forum section page."""
        section = response.meta["section"]
        self.logger.info(f"Parsing forum section: {section}")

        # Extract thread links
        thread_links = response.css('.thread-title a::attr(href)').getall()

        for link in thread_links:
            yield scrapy.Request(
                url=response.urljoin(link),
                callback=self.parse_thread,
                meta={"section": section},
            )

        # Check for pagination
        next_page = response.css('.pagination-next::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_forum,
                meta={"section": section},
            )

    def parse_thread(self, response):
        """Parse forum thread page."""
        self.logger.info(f"Parsing thread: {response.url}")

        # Extract thread data
        title = response.css('.thread-title::text').get()
        author = response.css('.author-name::text').get()
        author_url = response.css('.author-name::attr(href)').get()
        date = response.css('.post-date::text').get()
        content = response.css('.post-content').get()

        # Extract all replies
        replies = response.css('.reply')
        reply_data = []

        for reply in replies:
            reply_author = reply.css('.author-name::text').get()
            reply_author_url = reply.css('.author-name::attr(href)').get()
            reply_date = reply.css('.post-date::text').get()
            reply_content = reply.css('.reply-content').get()

            reply_data.append({
                "author": reply_author.strip() if reply_author else None,
                "author_url": response.urljoin(reply_author_url) if reply_author_url else None,
                "date": reply_date.strip() if reply_date else None,
                "content": self.clean_content(reply_content),
            })

        yield {
            "url": response.url,
            "title": title.strip() if title else None,
            "author": author.strip() if author else None,
            "author_url": response.urljoin(author_url) if author_url else None,
            "date": date.strip() if date else None,
            "content": self.clean_content(content),
            "replies": reply_data,
            "reply_count": len(reply_data),
            "scraped_at": datetime.now().isoformat(),
            "search_term": response.meta.get("search_term"),
            "section": response.meta.get("section"),
        }

    def clean_content(self, content):
        """Clean HTML content to plain text."""
        if not content:
            return None

        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', content)

        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()

        # Remove common BiggerPockets UI elements
        clean = re.sub(r'Click to expand\.\.\.', '', clean)
        clean = re.sub(r'Quote:', '', clean)

        return clean if clean else None

    def closed(self, reason):
        """Called when spider closes."""
        self.logger.info(f"Spider closed: {reason}")
