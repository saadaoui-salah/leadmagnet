import json
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

    def __init__(self, mapbound=None, listing_type="rent", **kwargs):
        super().__init__(**kwargs)
        print(self.name)
        if self.name == "zillow":
            if listing_type not in FILTERS:
                raise ValueError(f"Unknown listing type: {listing_type}. Choose from: rent, sold, sale")
            self.listing_type = listing_type
            self.FILTER_STATE = FILTERS[listing_type]

        if not mapbound:
            raise ValueError('mapbound argument required. Format: \'{"south":47.59,"west":-122.35,"north":47.63,"east":-122.31}\'')

        try:
            self.map_bounds = json.loads(mapbound)
        except json.JSONDecodeError:
            raise ValueError("mapbound must be valid JSON")

        required = ["south", "west", "north", "east"]
        for key in required:
            if key not in self.map_bounds:
                raise ValueError(f"mapbound missing required key: {key}")

        self.logger.info("Scraping [%s] bounds=%s", listing_type, self.map_bounds)

    async def start(self):
        yield self._build_request(1, self.map_bounds)

    def _build_request(self, page, map_bounds):
        return scrapy.Request(
            self.API_URL,
            method="PUT",
            body=json.dumps(self._payload(page, map_bounds)),
            callback=self.parse,
            cb_kwargs={"page": page, "map_bounds": map_bounds},
            dont_filter=True,
        )

    def _payload(self, page, map_bounds):
        return {
            "searchQueryState": {
                "pagination": {"currentPage": page},
                "isMapVisible": False,
                "mapBounds": map_bounds,
                "mapZoom": self.MAP_ZOOM,
                "filterState": self.FILTER_STATE,
                "isListVisible": True,
            },
            "wants": {"cat1": ["listResults"]},
            "requestId": self.REQUEST_ID_START + page - 1,
        }

    def parse(self, response, page, map_bounds):
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
            yield self._build_request(page + 1, map_bounds)

    def _parse_listing(self, data):
        item = ZillowListing()

        zpid = str(data.get("zpid", ""))

        item["source"] = "zillow"
        item["zpid"] = zpid
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

        units = data.get("units", [])
        min_rent = data.get("minBaseRent")
        max_rent = data.get("maxBaseRent")

        if not min_rent and units:
            rents = []
            for u in units:
                price_str = u.get("price", "")
                price_str = price_str.replace("$", "").replace(",", "").replace("+", "")
                try:
                    rents.append(int(price_str))
                except ValueError:
                    pass
            if rents:
                min_rent = min(rents)
                max_rent = max(rents)

        carousel = data.get("carouselPhotosComposable", {})
        photos = [carousel['baseUrl'].format(photoKey=photo.get("photoKey")) for photo in carousel.get("photoData", [])]

        hdp = data.get("hdpData", {})
        home_info = hdp.get("homeInfo", {})

        days_on_zillow = None
        rent_zestimate = None
        if home_info:
            days_on_zillow = home_info.get("daysOnZillow")
            rent_zestimate = home_info.get("rentZestimate")

        item["snapshot"] = {
            "status_type": data.get("statusType", ""),
            "status_text": data.get("statusText", ""),
            "min_rent": min_rent,
            "max_rent": max_rent,
            "availability_count": data.get("availabilityCount"),
            "availability_date": data.get("availabilityDate", ""),
            "photo_urls": photos,
            "has_3d_model": data.get("has3DModel", False),
            "is_featured_listing": data.get("isFeaturedListing", False),
            "days_on_zillow": days_on_zillow,
            "rent_zestimate": rent_zestimate,
            "units": [
                {"beds": u.get("beds"), "price": u.get("price", ""), "room_for_rent": u.get("roomForRent", False)}
                for u in units
            ],
        }

        return item
