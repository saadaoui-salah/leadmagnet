import json
from datetime import datetime

import scrapy
from core.items import ZillowDetailItem

GRAPHQL_HASH = "0526f7247361b0a89fd05a913cd382c93d5ec4d89e0284a0682eacc17378729e"
GRAPHQL_URL = "https://www.zillow.com/graphql/"


class ZillowDetailSpider(scrapy.Spider):
    name = "zillow_detail"

    custom_settings = {
            "ROBOTSTXT_OBEY": False,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
            "CONCURRENT_REQUESTS": 1,
            "DOWNLOAD_DELAY": 5,
            "RETRY_TIMES": 15,
            "ITEM_PIPELINES": {
                "core.pipelines.DjangoDetailUploadPipeline": 300,
                "core.pipelines.DjangoUploadPipeline": None,
            },
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

    def __init__(self, limit=None, **kwargs):
        super().__init__(**kwargs)
        self.dashboard_url = 'http://212.85.17.52:81'
        self.limit = int(limit) if limit else None

    async def start(self):
        zpids = await self._fetch_zpids()
        self.logger.info("Loaded %d zpids to scrape", len(zpids))
        for zpid in zpids:
            yield self._build_request(zpid)

    async def _fetch_zpids(self):
        import urllib.request
        url = f"{self.dashboard_url}/api/properties/zpids/?source=zillow"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            zpids = data.get("zpids", [])
            self.logger.info("Fetched %d zpids from backend", len(zpids))
        except Exception as e:
            self.logger.error("Failed to fetch zpids: %s", e)
            return []
        return zpids[:self.limit] if self.limit else zpids

    def _build_request(self, zpid):
        payload = {
            "variables": {
                "zpid": zpid,
                "zillowPlatform": "DESKTOP",
                "altId": None,
                "skipVsxProperty": False,
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": GRAPHQL_HASH,
                }
            },
        }
        return scrapy.Request(
            GRAPHQL_URL,
            method="POST",
            body=json.dumps(payload),
            callback=self.parse,
            cb_kwargs={"zpid": zpid},
            dont_filter=True,
        )

    def parse(self, response, zpid):
        if response.status != 200:
            self.logger.warning("zpid %s: HTTP %d", zpid, response.status)
            return

        data = json.loads(response.text)
        prop = data.get("data", {}).get("property")
        if not prop:
            self.logger.warning("No data for zpid %s", zpid)
            return

        item = ZillowDetailItem()
        item["zpid"] = str(zpid)
        item["lotId"] = str(zpid)

        item["bedrooms"] = prop.get("bedrooms")
        item["bathrooms"] = prop.get("bathrooms")
        item["living_area"] = prop.get("livingArea")
        item["lot_size"] = prop.get("lotSize")
        item["year_built"] = prop.get("yearBuilt")
        item["property_type_detailed"] = prop.get("homeType", "")

        reso = prop.get("resoFacts") or {}
        item["parking_features"] = reso.get("parkingFeatures", [])
        item["cooling"] = reso.get("cooling") or ""
        item["heating"] = reso.get("heating") or ""
        item["flooring"] = reso.get("flooring") or ""
        item["appliances"] = reso.get("appliances", [])
        item["interior_features"] = reso.get("interiorFeatures") or ""
        item["exterior_features"] = reso.get("exteriorFeatures") or ""
        item["lot_features"] = reso.get("lotFeatures") or ""
        item["sewer"] = reso.get("sewer") or ""
        item["water_source"] = reso.get("waterSource") or ""
        item["architectural_style"] = reso.get("architecturalStyle") or ""
        item["garage_spaces"] = reso.get("garageSpaces")
        item["hoa_fee"] = prop.get("monthlyHoaFee")
        item["total_fees"] = reso.get("associationFee")
        item["zestimate"] = prop.get("zestimate")
        item["property_tax_rate"] = prop.get("propertyTaxRate")
        item["description"] = prop.get("description") or ""
        item['parcel_id'] = prop.get("parcelId")
        item["price_history"] = [
            {
                "date": datetime.fromtimestamp(e["time"] / 1000).strftime("%Y-%m-%d"),
                "price": e.get("price") or 0,
                "price_per_sqft": e.get("pricePerSquareFoot"),
                "event": e.get("event", ""),
                "source": e.get("source", ""),
            }
            for e in prop.get("priceHistory", [])
            if e.get("time")
        ]

        item["tax_history"] = [
            {
                "date": datetime.fromtimestamp(e["time"] / 1000).strftime("%Y-%m-%d"),
                "tax_amount": int(e.get("taxPaid") or 0),
                "value": int(e.get("value") or 0),
                "year": datetime.fromtimestamp(e["time"] / 1000).year,
            }
            for e in prop.get("taxHistory", [])
            if e.get("time")
        ]

        item["schools"] = [
            {
                "name": s.get("name", ""),
                "rating": s.get("rating"),
                "type": "",
                "level": s.get("level", ""),
                "grades": s.get("grades", ""),
                "students_count": s.get("enrollment"),
                "teacher_count": None,
                "student_teacher_ratio": s.get("studentTeacherRatio"),
                "distance": s.get("distance"),
                "is_assigned": True,
            }
            for s in prop.get("assignedSchools", [])
        ]
        item['units'] = [
            {
                "listing_type":u.get("listingType", ""),
                "unit_id": u.get("zpid", ""),
                "bedrooms": u.get("beds"),
                "bathrooms": u.get("baths"),
                "sqft": u.get("sqft"),
                "price": u.get("price"),
                "sold_at": u.get("lastSoldAt"),
            }
            for u in prop.get("ungroupedUnits", [])
        ]

        self.logger.info("Scraped lotId %s: %s", zpid, prop.get("streetAddress", ""))
        yield item
