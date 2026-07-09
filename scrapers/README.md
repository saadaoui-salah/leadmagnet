# Atlanta Real Estate Scraper System

Scrapy-based scrapers for Atlanta real estate data with multi-provider proxy support.

## Features

- **Multi-provider proxy support**: Webshare and Oxylabs with class-level configuration
- **Cost tracking**: Middleware calculates proxy costs and displays in spider stats
- **Atlanta zip codes**: Targets highest-traffic areas from Reddit research
- **BiggerPockets leads**: Scrapes potential customers for market reports

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure proxies** in `.env`:
   ```env
   # Webshare
   WEBSHARE_API_TOKEN=your_token_here

   # Oxylabs
   OXYLABS_HOST=dc.oxylabs.io
   OXYLABS_PORT=8000
   OXYLABS_USER=your_user
   OXYLABS_PASS=your_pass
   ```

3. **Enable proxies** in `core/settings.py`:
   ```python
   PROXY_ENABLED = True
   PROXY_PROVIDER = "webshare"  # or "oxylabs"
   PROXY_TYPE = "datacenter"
   ```

## Available Spiders

### `atlanta_zillow`
Scrapes Zillow for Atlanta property listings.

```bash
scrapy crawl atlanta_zillow
scrapy crawl atlanta_zillow -a zip_codes=30318,30310
```

### `atlanta_redfin`
Scrapes Redfin for Atlanta market data.

```bash
scrapy crawl atlanta_redfin
scrapy crawl atlanta_redfin -a session=premium
```

### `biggerpockets_leads`
Scrapes BiggerPockets forums for Atlanta investor leads.

```bash
scrapy crawl biggerpockets_leads
```

### `proxy_example`
Test proxy connectivity.

```bash
scrapy crawl proxy_example
```

## Proxy Configuration

### Spider Class Variables

Override settings per-spider:

```python
class MySpider(scrapy.Spider):
    proxy_provider = "oxylabs"
    proxy_session = "premium"
    proxy_rotation = "random"
    proxy_location = "US"
    proxy_type = "residential"
```

### Named Sessions

Configure in `core/settings.py`:

```python
PROXY_SESSIONS = {
    "default": {
        "strategy": "round-robin",
        "country": "ZZ",
        "mode": "direct",
    },
    "premium": {
        "strategy": "random",
        "country": "US",
        "mode": "direct",
    },
}
```

## Cost Tracking

The `ProxyCostCalculatorMiddleware` tracks:
- Bandwidth per request
- Requests per provider
- Estimated cost based on provider pricing

Pricing (2026):
- **Webshare**: $0.03/proxy/month (datacenter), $3.50/GB (residential)
- **Oxylabs**: $1.20/IP/month (datacenter), $6.00/GB (residential)

View cost stats in spider output:
```bash
scrapy crawl atlanta_zillow -s STATS_DUMP=1
```

## Atlanta Zip Codes

Targeted areas (highest Reddit activity):
- **Top tier**: 30318, 30310, 30349, 30317
- **Midtown/Buckhead**: 30306, 30307, 30308, 30309
- **South/West**: 30312, 30313, 30314, 30316
- **North**: 30319, 30324, 30326, 30327
- **Outer areas**: 30329, 30332, 30338, 30340, 30341, 30342, 30345, 30346, 30350

## Output

Scrapers output JSON files to `output/` directory:
- `zillow_YYYY-MM-DD.json`
- `redfin_YYYY-MM-DD.json`
- `biggerpockets_leads_YYYY-MM-DD.json`
