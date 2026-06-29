# Lead Magnet Backend API Documentation

Base URL: `https://realestate-leadmagnet.onrender.com`

---

## Health Check

```
GET /health/
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "properties": 14317,
  "zipcodes": 46
}
```

---

## Data Ingestion

### POST /api/ingest/
Upload a single property listing.

**Request Body:**
```json
{
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "zipcode": "10001",
  "source": "zillow",
  "property_type": "apartment",
  "building_name": "The Manhattan",
  "street": "123 Main St",
  "min_rent": 3500,
  "bedrooms": 2,
  "bathrooms": 1,
  "sqft": 900,
  "management_company": "ABC Realty"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "zipcode": "10001",
  "source": "zillow",
  ...
}
```

---

### POST /api/ingest/bulk/
Upload multiple property listings.

**Request Body:**
```json
[
  { "address": "...", "city": "...", ... },
  { "address": "...", "city": "...", ... }
]
```

**Response:** `201 Created`
```json
{
  "created": 2,
  "errors": 0,
  "error_details": []
}
```

---

## Properties

### GET /api/properties/
List all properties with optional filters.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `source` | string | Filter by source (`zillow`, `realtor`, `redfin`) |
| `city` | string | Filter by city (partial match) |
| `state` | string | Filter by state (partial match) |
| `zipcode` | string | Filter by exact zipcode |
| `property_type` | string | Filter by type (`apartment`, `house`, etc.) |
| `management_company` | string | Filter by management company |
| `search` | string | Search address, street, building name |
| `page` | int | Page number |
| `page_size` | int | Results per page |

**Example:**
```
GET /api/properties/?zipcode=10001&source=zillow&page_size=20
```

---

### GET /api/properties/{id}/
Get single property detail.

---

### POST /api/properties/
Create a new property.

### PUT /api/properties/{id}/
Update a property.

### DELETE /api/properties/{id}/
Delete a property.

---

## Zipcodes

### GET /api/zipcodes/
List all zipcodes with optional filters.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `zipcode` | string | Filter by exact zipcode |
| `city` | string | Filter by city |
| `state` | string | Filter by state |

---

### GET /api/zipcodes/all/
Get all zipcodes with count.

**Response:**
```json
{
  "count": 46,
  "results": [
    {
      "id": 1,
      "zipcode": "10001",
      "city": "New York",
      "state": "NY",
      "south": 40.740,
      "west": -73.997,
      "north": 40.749,
      "east": -73.988,
      "population": 55000,
      "median_income": 85000,
      "median_home_value": 1200000
    }
  ]
}
```

---

### GET /api/zipcodes/geojson/
Get all zipcodes as GeoJSON (for map rendering).

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-73.997, 40.740], [-73.988, 40.749], ...]]
      },
      "properties": {
        "zipcode": "10001",
        "city": "New York",
        "state": "NY",
        "center_lat": 40.7445,
        "center_lng": -73.9925
      }
    }
  ]
}
```

---

### GET /api/zipcodes/lookup/
Find zipcodes containing a lat/lng point.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `lat` | float | Yes | Latitude |
| `lng` | float | Yes | Longitude |

**Example:**
```
GET /api/zipcodes/lookup/?lat=40.744&lng=-73.992
```

---

## Property Snapshots

### GET /api/snapshots/
List property snapshots (daily price/availability data).

### GET /api/snapshots/{id}/
Get single snapshot detail.

---

## Market Metrics

### GET /api/state-metrics/
List state-level daily metrics.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `state` | string | Filter by state code |

**Response (top 100 by date):**
```json
[
  {
    "id": 1,
    "state": "NY",
    "date": "2026-06-24",
    "avg_rent": 4500,
    "total_listings": 14000,
    "rent_change_pct": 4.2,
    "inventory_change_pct": -8.5
  }
]
```

---

### GET /api/zip-rankings/
List zipcode rankings by rent growth.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `date` | string | Filter by date (YYYY-MM-DD) |

**Response (top 50 by rent growth):**
```json
[
  {
    "id": 1,
    "zipcode": "10022",
    "date": "2026-06-24",
    "rent_growth_rank": 1,
    "rent_growth_pct": 14.2,
    "avg_rent": 5200
  }
]
```

---

### GET /api/market-events/
List market events.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `event_type` | string | Filter by type (`rent_surge`, `inventory_up`, etc.) |
| `posted_to_linkedin` | string | Filter by `true`/`false` |

---

## Analytics Endpoints

### GET /api/analytics/top-rent-growth/
Top zipcodes by rent growth.

**Query Parameters:**
| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 10 | Number of results |
| `days` | 30 | Lookback period |

**Response:**
```json
[
  {
    "zip": "10022",
    "city": "New York",
    "state": "NY",
    "rent_growth": 14.2,
    "avg_rent": 5200,
    "active_listings": 340
  }
]
```

---

### GET /api/analytics/biggest-drops/
Top zipcodes with biggest rent decreases.

**Query Parameters:** Same as `top-rent-growth`.

---

### GET /api/analytics/inventory-explosion/
Zipcodes with large inventory increases.

**Query Parameters:**
| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 10 | Number of results |
| `min_growth` | 20 | Minimum inventory growth % |

---

### GET /api/analytics/investor-opportunities/
Best investment opportunities by yield.

**Query Parameters:**
| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 10 | Number of results |

---

### GET /api/analytics/emerging-markets/
Emerging markets with growing demand.

---

### GET /api/analytics/hidden-gems/
Undervalued zipcodes with high potential.

---

### GET /api/analytics/yield-report/
Rental yield analysis by zipcode.

---

### GET /api/analytics/luxury-markets/
High-end market analysis.

---

### GET /api/analytics/top-landlords/
Top property management companies.

---

### GET /api/analytics/market-pulse/
Overall market health indicator.

---

### GET /api/analytics/daily-digest/
Daily market summary.

---

### GET /api/analytics/rent-history/{zipcode}/
Rent history for a specific zipcode.

**Example:**
```
GET /api/analytics/rent-history/10001/
```

---

### GET /api/analytics/opportunity-score/
Investment opportunity scores.

---

### GET /api/analytics/state-summary/
State-level market summary.

---

### GET /api/analytics/building-performance/
Building-level performance metrics.

---

### GET /api/analytics/daily-report/
Full daily report for a zipcode.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `zipcode` | string | Yes | Target zipcode |

**Example:**
```
GET /api/analytics/daily-report/?zipcode=10001
```

**Response:**
```json
{
  "zipcode": "10001",
  "city": "New York",
  "state": "NY",
  "date": "2026-06-24",
  "marketOverview": {
    "totalListings": 14317,
    "totalListingsChange": 14.0,
    "avgRent": 4504,
    "avgRentChange": 4.0,
    "medianHomeValue": 1200000,
    "medianHomeValueChange": 3.1,
    "newListingsWeek": 847,
    "newListingsChange": 10.2
  },
  "rentTrends": {
    "labels": ["2026-06-01", "2026-06-08", ...],
    "values": [4200, 4350, 4504, ...]
  },
  "supplyDemand": {
    "labels": ["10001", "10002", ...],
    "newListings": [200, 150, ...],
    "propertiesSold": [180, 120, ...],
    "inventoryChangePct": -8.5
  },
  "priceMovement": {
    "labels": [...],
    "values": [...]
  },
  "topGrowingZips": [...],
  "rentalBreakdown": [...],
  "topProperties": [...],
  "investorScores": {
    "demand": 82,
    "competition": 65,
    "yield": 71,
    "overall": 74
  },
  "marketEvents": [...]
}
```

---

## Smart ZIP Pick

### GET /api/analytics/smart-zip-pick/
Automatically pick the most powerful zip code for analysis based on composite scoring.

**Scoring Methodology:**
- **Growth (0-40 pts):** Rent growth % × 3
- **Volume (0-25 pts):** Listings / 100 × 25
- **Demand (0-20 pts):** Inventory compression × 2
- **Yield (0-15 pts):** Rent-to-price ratio × 2

**Response:**
```json
{
  "winner": {
    "zipcode": "10022",
    "city": "New York",
    "state": "NY",
    "score": 78.5,
    "breakdown": {
      "growth": 40,
      "volume": 22,
      "demand": 12,
      "yield": 4.5
    },
    "metrics": {
      "avg_rent": 5200,
      "rent_growth": 14.2,
      "active_listings": 412,
      "inventory_change": -8.5,
      "median_home_value": 1285000,
      "population": 45000
    }
  },
  "runner_ups": [...],
  "total_zipcodes_analyzed": 46,
  "scoring_methodology": {...}
}
```

---

## Stats

### GET /api/stats/
Get overall property statistics.

**Response:**
```json
{
  "total_properties": 14317,
  "by_source": {
    "zillow": 12000,
    "realtor": 1500,
    "redfin": 817
  }
}
```

---

## Rate Limits

No explicit rate limits, but be respectful. Bulk ingestion should batch requests (max 100 per call).

## Authentication

All endpoints are currently public (`AllowAny`). No authentication required.
