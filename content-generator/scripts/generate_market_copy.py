#!/usr/bin/env python3
"""
Fetch market data from backend API and generate carousel copy via Ollama Llama.
Uses smart-zip-pick to automatically select the best zipcode for analysis.
Outputs JSON that content-generator can consume.
"""

import json
import os
import urllib.request
import sys

BACKEND_API = "http://127.0.0.1:8000"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:32b"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def pick_best_zipcode():
    """Use smart-zip-pick to find the best zipcode for analysis."""
    print("[API] Picking best zipcode for analysis...")
    try:
        result = fetch_json(f"{BACKEND_API}/api/analytics/smart-zip-pick/")
        winner = result.get("winner", {})
        zipcode = winner.get("zipcode", "10001")
        score = winner.get("score", 0)
        print(f"[API] Best zipcode: {zipcode} (score: {score})")
        return zipcode, winner
    except Exception as e:
        print(f"[API] Smart-zip-pick failed: {e}, using default 10001")
        return "10001", {}


def fetch_market_data(zipcode="10001"):
    print(f"[API] Fetching market data for {zipcode}...")
    market = fetch_json(f"{BACKEND_API}/api/analytics/generate-market-data/?zipcode={zipcode}")

    city = market.get("city", "New York")
    state = market.get("state", "NY")
    median_rent = market.get("medianRent", 0)
    active_listings = market.get("activeListings", 0)
    rent_growth = market.get("rentGrowth30d", 0)
    median_home = market.get("medianHomePrice", 0)
    avg_days = market.get("avgDaysOnMarket", 0)
    new_listings = market.get("newListingsChange", 0)
    inventory_change = market.get("inventoryChangePct", 0)
    investor = market.get("investorScores", {})
    rental = market.get("rentalBreakdown", [])
    top_zips = market.get("topZipCodes", [])
    trends = market.get("trends", [])

    # Build rental breakdown text
    rental_lines = []
    for r in rental:
        rental_lines.append(f"  - {r['type']}: ${r['avgRent']:,} ({r['count']} units)")

    # Build top zips text
    zip_lines = []
    for z in top_zips[:5]:
        zip_lines.append(
            f"  - {z.get('zipCode', '')}: avg rent ${z.get('medianRent', 0):,}, "
            f"growth +{z.get('rentGrowth30d', 0)}%, {z.get('activeListings', 0)} listings"
        )

    return {
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "median_rent": median_rent,
        "active_listings": active_listings,
        "rent_growth_30d": rent_growth,
        "median_home_price": median_home,
        "avg_days_on_market": avg_days,
        "new_listings_change": new_listings,
        "inventory_change_pct": inventory_change,
        "investor_scores": investor,
        "rental_breakdown": rental_lines,
        "top_zips": zip_lines,
        "trends": trends,
    }


def build_prompt(data, winner_info=None):
    zip_list = "\n".join(data["top_zips"]) if data["top_zips"] else "  (no zip code data available)"
    rental_list = "\n".join(data["rental_breakdown"]) if data["rental_breakdown"] else "  (no rental breakdown available)"

    trends_text = ""
    if data["trends"]:
        trends_lines = []
        for t in data["trends"]:
            trends_lines.append(f"  - {t.get('label', '')}: median rent ${t.get('rent', 0):,}, "
                                f"{t.get('inventory', 0)} listings, {t.get('daysOnMarket', 0)} days on market")
        trends_text = "\nRENT TRENDS (last " + str(len(data["trends"])) + " data points):\n" + "\n".join(trends_lines)

    winner_context = ""
    if winner_info and winner_info.get("zipcode"):
        metrics = winner_info.get("metrics", {})
        breakdown = winner_info.get("breakdown", {})
        winner_context = f"""
THIS IS THE HIGHEST-SCORING ZIPCODE (score: {winner_info.get('score', 0)}/100):
- ZIP: {winner_info.get('zipcode')}
- City: {winner_info.get('city')}, {winner_info.get('state')}
- Avg Rent: ${metrics.get('avg_rent', 0):,}
- Rent Growth: {metrics.get('rent_growth', 0)}%
- Active Listings: {metrics.get('active_listings', 0):,}
- Inventory Change: {metrics.get('inventory_change', 0)}%
- Median Home Value: ${metrics.get('median_home_value', 0):,}
- Scoring: Growth={breakdown.get('growth', 0)}, Volume={breakdown.get('volume', 0)}, Demand={breakdown.get('demand', 0)}, Yield={breakdown.get('yield', 0)}
"""

    investor = data.get("investor_scores", {})
    investor_text = ""
    if investor:
        investor_text = f"""
INVESTOR SCORES (0-100):
- Demand: {investor.get('demand', 0)}
- Competition: {investor.get('competition', 0)}
- Yield: {investor.get('yield', 0)}
- Overall: {investor.get('overall', 0)}
"""

    return f"""You are a real estate market intelligence copywriter for LinkedIn/Instagram carousels.
Generate engaging, data-driven copy for a 10-slide carousel. Be punchy, authoritative, and specific.

MARKET DATA:
- City: {data['city']}, {data['state']}
- ZIP: {data['zipcode']}
- Median Rent: ${data['median_rent']:,}
- Active Listings: {data['active_listings']:,}
- 30-Day Rent Growth: {data['rent_growth_30d']}%
- Median Home Price: ${data['median_home_price']:,}
- Avg Days on Market: {data['avg_days_on_market']}
- New Listings Change: {data['new_listings_change']}%
- Inventory Change: {data['inventory_change_pct']}%
{winner_context}{investor_text}
RENTAL BREAKDOWN BY UNIT TYPE:
{rental_list}
TOP GROWING ZIPS:
{zip_list}{trends_text}

Generate a JSON object with these fields (no markdown, just raw JSON):
{{
  "hook": "A punchy 5-8 word headline using REAL numbers from the data (e.g. 'Miami Rents Up 18% to $4,464')",
  "hookSub": "One line with real stats (e.g. '3,091 active listings • ZIP 33139 • June 2026')",
  "curiosity": "A 1-2 sentence insight that makes people swipe (slide 2)",
  "snapshotTitle": "Title for the market snapshot slide (slide 3)",
  "rentTrendInsight": "1-2 sentences explaining why rent trend matters using real numbers (slide 4)",
  "priceTrendInsight": "1-2 sentences on price movement using real numbers (slide 5)",
  "investorInsight1": "First investor insight panel text using real scores (slide 7)",
  "investorInsight2": "Second investor insight panel text using real zip data (slide 7)",
  "investorInsight3": "Third investor insight panel text using real data (slide 7)",
  "riskSignal": "1-2 sentences on risk/affordability using real numbers (slide 8)",
  "inventoryRisk": "ONE punchy sentence (max 15 words). State the INVENTORY NUMBER and what happens next. Do NOT start with 'If'. Example style: 'Inventory flat at 0% — one new listing surge away from a rent cool-down.'",
  "executionRisk": "ONE punchy sentence (max 15 words). State the DAYS ON MARKET and the speed risk. Do NOT start with 'Fast' or 'At'. Example style: '18-day turnover leaves no room for slow offers.'",
  "watchSupply": "ONE punchy sentence (max 15 words). State what inventory direction means. Do NOT start with 'A second'. Example style: 'Zero inventory movement means landlords still hold the leverage.'",
  "watchNext": "What to watch going forward (slide 9)",
  "prediction": "Short market prediction (slide 9)",
  "ctaHeadline": "CTA headline for slide 10",
  "ctaSub": "CTA supporting text"
}}

CRITICAL: Use the EXACT numbers from the data above. Do NOT make up or round numbers. Be punchy and specific. No generic statements."""


def generate_with_ollama(prompt):
    print("[Ollama] Generating copy with qwen2.5:32b...")
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read())

    response_text = result.get("response", "")

    # Try to extract JSON from response
    import re

    # First try: find JSON in code blocks
    code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Second try: find raw JSON
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

    return {"raw_response": response_text}


def build_zillow_market_data(data, generated_copy, winner_info=None):
    """Build market data using the SAME data that was in the prompt."""
    # Use the data dict that was already used to build the prompt
    # This ensures generatedCopy references match the actual numbers
    market = {
        "city": data["city"],
        "state": data["state"],
        "zipCode": data["zipcode"],
        "generatedAt": "2026-06-28",
        "activeListings": data["active_listings"],
        "medianRent": data["median_rent"],
        "medianHomePrice": data["median_home_price"],
        "monthlyGrowth": data["rent_growth_30d"],
        "yearlyGrowth": 0,
        "rentGrowth30d": data["rent_growth_30d"],
        "homeGrowth30d": 0,
        "avgDaysOnMarket": data["avg_days_on_market"],
        "newListingsChange": data["new_listings_change"],
        "inventoryChangePct": data["inventory_change_pct"],
        "investorScores": data.get("investor_scores", {"demand": 0, "competition": 0, "yield": 0, "overall": 0}),
        "rentalBreakdown": [],
        "topZipCodes": [],
        "trends": data.get("trends", []),
        "generatedCopy": generated_copy,
        "winnerInfo": winner_info,
    }

    # Fetch enrichment data (rental breakdown, top zips, rent drops)
    try:
        market_api = fetch_json(f"{BACKEND_API}/api/analytics/generate-market-data/?zipcode={data['zipcode']}")
        if market_api:
            market["rentalBreakdown"] = market_api.get("rentalBreakdown", [])
            market["topZipCodes"] = market_api.get("topZipCodes", [])
            market["medianHomePrice"] = market_api.get("medianHomePrice", market["medianHomePrice"])
            market["homeGrowth30d"] = market_api.get("homeGrowth30d", 0)
    except Exception as e:
        print(f"[API] market-data enrichment failed: {e}")

    try:
        drops = fetch_json(f"{BACKEND_API}/api/analytics/rent-drops/?limit=10")
        market["rentDrops"] = drops if isinstance(drops, list) else []
    except Exception as e:
        print(f"[API] rent-drops fetch failed: {e}")
        market["rentDrops"] = []

    return market


def main():
    # Pick the best zipcode automatically
    zipcode, winner_info = pick_best_zipcode()

    # Fetch market data for the winning zipcode
    data = fetch_market_data(zipcode)

    # Generate copy with Ollama
    prompt = build_prompt(data, winner_info)
    generated_copy = generate_with_ollama(prompt)

    # Build final market data
    market_data = build_zillow_market_data(data, generated_copy, winner_info)

    # Save to JSON (resolve path relative to this script's directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "..", "src", "data", "generatedMarket.json")
    with open(output_path, "w") as f:
        json.dump(market_data, f, indent=2)

    print(f"\n[Done] Generated market data saved to {output_path}")
    print(f"[Copy] Hook: {generated_copy.get('hook', 'N/A')}")
    print(f"[Copy] CTA: {generated_copy.get('ctaHeadline', 'N/A')}")

    return market_data


if __name__ == "__main__":
    main()
