#!/usr/bin/env python3
"""
Zyte Scrapy Cloud job runner with duplicate prevention.
Checks pending/running jobs before scheduling new ones.

Usage:
    python run_zyte.py                          # Run zillow search spider (all types, all zips)
    python run_zyte.py --spider detail          # Run zillow_detail spider (batched)
    python run_zyte.py --spider detail --batch 0-5  # Run detail batches 0-5
    python run_zyte.py --listing-types rent      # Only rent listings
    python run_zyte.py --dry-run                 # Preview without submitting
"""

import json
import os
import sys
import time
import base64
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────
# CONFIG - Zillow Search Spider (Account 1)
# ──────────────────────────────────────────────────────────
ZYTE_API_KEY = os.environ.get("ZYTE_API_KEY", "")
ZYTE_PROJECT_ID = os.environ.get("ZYTE_PROJECT_ID", "")
ZYTE_RUN_URL = "https://app.zyte.com/api/run.json"
ZYTE_JOBS_URL = "https://app.zyte.com/api/jobs/list.json"

BACKEND_API = os.environ.get("BACKEND_API")
ZIPCODES_URL = f"{BACKEND_API}/api/zipcodes/all/"

LISTING_TYPES = ["rent", "sold", "sale"]

# ──────────────────────────────────────────────────────────
# CONFIG - Zillow Detail Spider (Account 2)
# ──────────────────────────────────────────────────────────
ZYTE_DETAIL_API_KEY = os.environ.get("ZYTE_DETAIL_API_KEY", "84d09476d2df4b238e0e763b992195d7")
ZYTE_DETAIL_PROJECT_ID = os.environ.get("ZYTE_DETAIL_PROJECT_ID", "868681")

DETAIL_BATCH_SIZE = 2000
DETAIL_TOTAL_PROPERTIES = 55000


# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────
def zyte_auth_header(api_key):
    auth = base64.b64encode(f"{api_key}:".encode()).decode()
    return f"Basic {auth}"


def zyte_request(url, method="GET", data=None, api_key=None):
    """Make authenticated request to Zyte API."""
    if api_key is None:
        api_key = ZYTE_API_KEY
    headers = {"Authorization": zyte_auth_header(api_key)}
    if data and method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        body = urlencode(data).encode("utf-8")
    else:
        body = None

    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ──────────────────────────────────────────────────────────
# FETCH ZIPCODES FROM BACKEND
# ──────────────────────────────────────────────────────────
def fetch_zipcodes():
    req = Request(ZIPCODES_URL, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    results = data.get("results", data) if isinstance(data, dict) else data
    geo = {}
    for z in results:
        geo[z["zipcode"]] = {
            "south": z["south"],
            "west": z["west"],
            "north": z["north"],
            "east": z["east"],
        }
    print(f"[ZipCodes] Fetched {len(geo)} zipcodes")
    return geo


# ──────────────────────────────────────────────────────────
# CHECK EXISTING JOBS (pending + running)
# ──────────────────────────────────────────────────────────
def get_active_jobs(api_key=None, project_id=None):
    """Get all pending and running jobs."""
    if api_key is None:
        api_key = ZYTE_API_KEY
    if project_id is None:
        project_id = ZYTE_PROJECT_ID

    active = {}
    for state in ["pending", "running"]:
        url = f"{ZYTE_JOBS_URL}?project={project_id}&state={state}&count=1000"
        try:
            result = zyte_request(url, api_key=api_key)
            if result.get("status") == "ok":
                for job in result.get("jobs", []):
                    job_id = job.get("id", "")
                    tags = job.get("tags", [])
                    active[job_id] = {
                        "state": state,
                        "tags": tags,
                        "spider": job.get("spider", ""),
                    }
        except Exception as e:
            print(f"[Jobs] Error fetching {state} jobs: {e}")

    pending = sum(1 for j in active.values() if j['state'] == 'pending')
    running = sum(1 for j in active.values() if j['state'] == 'running')
    print(f"[Jobs] Found {len(active)} active jobs ({pending} pending, {running} running)")
    return active


def is_job_scheduled(active_jobs, tag):
    """Check if a job with this tag is already scheduled."""
    for job in active_jobs.values():
        if tag in job.get("tags", []):
            return True
    return False


# ──────────────────────────────────────────────────────────
# SCHEDULE ZILLOW SEARCH SPIDER
# ──────────────────────────────────────────────────────────
def run_search_spider(zipcode, listing_type):
    """Schedule a single Zillow search spider job."""
    tag = f"zillow-{listing_type}-{zipcode}"

    payload = {
        "project": ZYTE_PROJECT_ID,
        "spider": "zillow",
        "units": 1,
        "add_tag": tag,
        "zip_code": zipcode,
        "listing_type": listing_type,
    }

    try:
        result = zyte_request(ZYTE_RUN_URL, method="POST", data=payload)
        if result.get("status") == "ok":
            job_id = result.get("jobid", "unknown")
            print(f"  ✓ Scheduled: {job_id} [{listing_type}] ZIP {zipcode}")
            return True
        else:
            print(f"  ✗ Failed: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


# ──────────────────────────────────────────────────────────
# SCHEDULE ZILLOW DETAIL SPIDER
# ──────────────────────────────────────────────────────────
def run_detail_spider(batch_offset):
    """Schedule a single zillow_detail batch job."""
    tag = f"detail-batch-{batch_offset}"

    payload = {
        "project": ZYTE_DETAIL_PROJECT_ID,
        "spider": "zillow_detail",
        "units": 1,
        "add_tag": tag,
        "batch": str(DETAIL_BATCH_SIZE),
        "offset": str(batch_offset),
    }

    try:
        result = zyte_request(ZYTE_RUN_URL, method="POST", data=payload, api_key=ZYTE_DETAIL_API_KEY)
        if result.get("status") == "ok":
            job_id = result.get("jobid", "unknown")
            print(f"  ✓ Scheduled: {job_id} detail batch offset={batch_offset}")
            return True
        else:
            print(f"  ✗ Failed: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Zillow spiders on Zyte Cloud (with dedup)")
    parser.add_argument("--spider", choices=["search", "detail"], default="search",
                        help="Which spider to run (default: search)")
    parser.add_argument("--listing-types", nargs="+", choices=LISTING_TYPES, default=LISTING_TYPES,
                        help="Listing types to scrape (default: rent sold sale)")
    parser.add_argument("--zip", type=str, help="Comma-separated zip codes (default: all from backend)")
    parser.add_argument("--batch", type=str,
                        help="Detail spider: batch range like '0-5' or comma-separated '0,2000,4000'")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scheduled without running")
    parser.add_argument("--force", action="store_true", help="Skip duplicate check, run all jobs")
    args = parser.parse_args()

    if args.spider == "detail":
        return run_detail(args)
    else:
        return run_search(args)


def run_search(args):
    """Run zillow search spider."""
    if not ZYTE_API_KEY:
        print("[Error] ZYTE_API_KEY not set")
        sys.exit(1)
    if not ZYTE_PROJECT_ID:
        print("[Error] ZYTE_PROJECT_ID not set")
        sys.exit(1)

    try:
        geo = fetch_zipcodes()
    except Exception as e:
        print(f"[Error] Could not fetch zipcodes: {e}")
        sys.exit(1)

    if args.zip:
        zip_codes = [z.strip() for z in args.zip.split(",")]
    else:
        zip_codes = list(geo.keys())

    if not args.force:
        active_jobs = get_active_jobs()
    else:
        active_jobs = {}

    total = len(zip_codes) * len(args.listing_types)
    scheduled = 0
    skipped = 0
    failed = 0

    print(f"\n[Run] {total} jobs to process ({len(args.listing_types)} types x {len(zip_codes)} zipcodes)")
    print(f"[Run] Listing types: {', '.join(args.listing_types)}")
    if args.force:
        print("[Run] Force mode: skipping duplicate check\n")

    for listing_type in args.listing_types:
        print(f"\n{'='*50}")
        print(f"  {listing_type.upper()} JOBS")
        print(f"{'='*50}")

        for i, zipcode in enumerate(zip_codes, 1):
            if zipcode not in geo:
                print(f"  [{i}/{len(zip_codes)}] ZIP {zipcode}: unknown, skipping")
                failed += 1
                continue

            tag = f"zillow-{listing_type}-{zipcode}"
            if not args.force and is_job_scheduled(active_jobs, tag):
                print(f"  [{i}/{len(zip_codes)}] ZIP {zipcode}: already scheduled, skipping")
                skipped += 1
                continue

            if args.dry_run:
                print(f"  [{i}/{len(zip_codes)}] ZIP {zipcode}: would schedule [{listing_type}]")
                scheduled += 1
            else:
                print(f"  [{i}/{len(zip_codes)}] ZIP {zipcode}:")
                success = run_search_spider(zipcode, listing_type)
                if success:
                    scheduled += 1
                else:
                    failed += 1
                time.sleep(1)

    print(f"\n{'='*50}")
    print(f"  SUMMARY")
    print(f"{'='*50}")
    print(f"  Scheduled: {scheduled}")
    print(f"  Skipped (duplicate): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total: {total}")
    if args.dry_run:
        print(f"\n  [DRY RUN] No jobs were actually scheduled")
    return 0


def run_detail(args):
    """Run zillow_detail spider in batches."""
    if not ZYTE_DETAIL_API_KEY:
        print("[Error] ZYTE_DETAIL_API_KEY not set")
        sys.exit(1)
    if not ZYTE_DETAIL_PROJECT_ID:
        print("[Error] ZYTE_DETAIL_PROJECT_ID not set")
        sys.exit(1)

    # Parse batch range
    if args.batch:
        if "-" in args.batch:
            start, end = args.batch.split("-")
            offsets = list(range(int(start), int(end) + 1, DETAIL_BATCH_SIZE))
        else:
            offsets = [int(x.strip()) for x in args.batch.split(",")]
    else:
        offsets = list(range(0, DETAIL_TOTAL_PROPERTIES, DETAIL_BATCH_SIZE))

    if not args.force:
        active_jobs = get_active_jobs(api_key=ZYTE_DETAIL_API_KEY, project_id=ZYTE_DETAIL_PROJECT_ID)
    else:
        active_jobs = {}

    scheduled = 0
    skipped = 0
    failed = 0

    print(f"\n[Detail] {len(offsets)} batches to process (batch_size={DETAIL_BATCH_SIZE})")
    if args.force:
        print("[Detail] Force mode: skipping duplicate check\n")

    for i, offset in enumerate(offsets, 1):
        tag = f"detail-batch-{offset}"
        if not args.force and is_job_scheduled(active_jobs, tag):
            print(f"  [{i}/{len(offsets)}] Batch offset={offset}: already scheduled, skipping")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  [{i}/{len(offsets)}] Batch offset={offset}: would schedule")
            scheduled += 1
        else:
            print(f"  [{i}/{len(offsets)}] Batch offset={offset}:")
            success = run_detail_spider(offset)
            if success:
                scheduled += 1
            else:
                failed += 1
            time.sleep(1)

    print(f"\n{'='*50}")
    print(f"  SUMMARY")
    print(f"{'='*50}")
    print(f"  Scheduled: {scheduled}")
    print(f"  Skipped (duplicate): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(offsets)}")
    if args.dry_run:
        print(f"\n  [DRY RUN] No jobs were actually scheduled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
