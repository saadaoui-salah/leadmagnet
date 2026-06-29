import json
import re
from urllib.parse import urljoin

import scrapy
from core.items import ZillowListing


FILTERS = {
    "rent": {
        "isForRent": {"value": True},
        "isForSaleByAgent": {"value": False},
        "isForSaleByOwner": {"value": False},
        "isNewConstruction": {"value": False},
        "isComingSoon": {"value": False},
        "isAuction": {"value": False},
        "isForSaleForeclosure": {"value": False},
    },
    "sold": {
        "isActiveStatus": {"value": False},
        "isAuction": {"value": False},
        "isComingSoon": {"value": False},
        "isComingSoonStatus": {"value": False},
        "isForSaleByAgent": {"value": False},
        "isForSaleByOwner": {"value": False},
        "isForSaleForeclosure": {"value": False},
        "isNewConstruction": {"value": False},
        "isRecentlySold": {"value": True},
        "isZillowPreview": {"value": False},
        "sortSelection": {"value": "globalrelevanceex"},
    },
    "sale": {
        "sortSelection": {"value": "globalrelevanceex"},
    },
}


class ZillowSpider(scrapy.Spider):
    name = "zillow"

    API_URL = "https://www.zillow.com/async-create-search-page-state"
    MAP_ZOOM = 7
    REQUEST_ID_START = 1

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "RETRY_TIMES": 15,
        "DOWNLOADER_MIDDLEWARES": {
            "core.middlewares.CurlCffiDownloaderMiddleware": 400,
            "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware":None,
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
        },
        "DEFAULT_REQUEST_HEADERS": {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.zillow.com",
            "referer": "https://www.zillow.com/homes/for_rent/",
            "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
        },
    }

    LISTING_TYPES = {
        "rentals": "rentals/",
        "sold": "sold/",
        "sale": "",
        "": "",
    }

    def __init__(self, zip_code=None, listing_type="sale", **kwargs):
        super().__init__(**kwargs)
        if not zip_code:
            raise ValueError("zip_code argument is required")
        if listing_type not in self.LISTING_TYPES:
            raise ValueError(f"Unknown listing_type: {listing_type}. Choose from: rentals, sold, sale")
        self.zip_code = zip_code
        self.listing_type = listing_type

    async def start(self):
        path = self.LISTING_TYPES[self.listing_type]
        url = f"https://www.zillow.com/{self.zip_code}/{path}"
        self.logger.info("Fetching %s", url)
        yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
        )
        if not match:
            self.logger.error("__NEXT_DATA__ not found for %s", self.zip_code)
            return

        data = json.loads(match.group(1))
        payload = data['props']['pageProps']['searchPageState']['queryState']
        yield self._build_request(1, payload)

    def _build_request(self, page, payload):
        return scrapy.Request(
            self.API_URL,
            method="PUT",
            body=json.dumps(self._payload(page, payload)),
            callback=self.parse_items,
            cb_kwargs={"page": page, "payload": payload},
            dont_filter=True,
        )

    def _payload(self, page, payload):
        return {
            "searchQueryState": {
                "pagination": {"currentPage": page},
                "isMapVisible": True,
                "mapBounds": payload["mapBounds"],
                "mapZoom": self.MAP_ZOOM,
                "regionSelection": payload["regionSelection"],
                "filterState": payload['filterState'],
                "isListVisible": True,
            },
            "wants": {"cat1": ["listResults"]},
            "requestId": self.REQUEST_ID_START + page - 1,
            "isDebugRequest": False,
        }

    def parse_items(self, response, page, payload):
        data = json.loads(response.text)

        if isinstance(data, list):
            data = data[0]

        cat1 = data.get("cat1", {})
        results = cat1.get("searchResults", {})
        list_results = results.get("listResults", [])

        for listing in list_results:
            item = self._parse_listing(listing)
            if item:
                yield item

        search_list = (
            results.get("searchList", {})
            or cat1.get("searchList", {})
            or data.get("searchList", {})
        )
        total_pages = search_list.get("totalPages", 0)
        total_results = search_list.get("totalResultCount", 0)

        self.logger.info(
            "Page %d: got %d listings | total=%d pages=%d",
            page, len(list_results), total_results, total_pages,
        )

        if page < total_pages:
            yield self._build_request(page + 1, payload)

    def _parse_listing(self, data):
        item = ZillowListing()

        lotId = str(data.get("lotId", ""))
        item["source"] = "zillow"
        item["lotId"] = lotId
        item["detail_url"] = urljoin("https://www.zillow.com", data.get("detailUrl", ""))
        item["building_name"] = data.get("buildingName", "")
        item["is_building"] = data.get("isBuilding", False)
        item["address"] = data.get("address", "")
        item["street"] = data.get("addressStreet", "")
        item["city"] = data.get("addressCity", "")
        item["state"] = data.get("addressState", "")
        item["zipcode"] = data.get("addressZipcode", "")
        lat_long = data.get("latLong", {})
        item["latitude"] = lat_long.get("latitude")
        item["longitude"] = lat_long.get("longitude")

        return item
