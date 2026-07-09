#!/usr/bin/env python3
"""
Zyte Scrapy Cloud job report.
Shows job stats per account: total, by type, items scraped, empty jobs.

Usage:
    python zyte_report.py              # Report for all accounts
    python zyte_report.py --days 7     # Last 7 days only
    python zyte_report.py --json       # Output as JSON
"""

import json
import os
import sys
import base64
import argparse
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

ZYTE_JOBS_URL = "https://app.zyte.com/api/jobs/list.json"
ZYTE_ITEMS_URL = "https://app.zyte.com/api/jobs/{job_id}/items.json"

ACCOUNTS = [
    {
        "name": "Account 1",
        "api_key": os.environ.get("ZYTE_API_KEY", ""),
        "project_id": os.environ.get("ZYTE_PROJECT_ID", ""),
    },
    {
        "name": "Account 2 (Detail)",
        "api_key": os.environ.get("ZYTE_DETAIL_API_KEY", "84d09476d2df4b238e0e763b992195d7"),
        "project_id": os.environ.get("ZYTE_DETAIL_PROJECT_ID", "868681"),
    },
]


def zyte_request(url, api_key):
    auth = base64.b64encode(f"{api_key}:".encode()).decode()
    req = Request(url, headers={"Authorization": f"Basic {auth}"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_jobs(api_key, project_id, state=None):
    all_jobs = []
    for s in (state or ["finished", "running", "pending"]):
        offset = 0
        while True:
            url = f"{ZYTE_JOBS_URL}?project={project_id}&state={s}&count=100&offset={offset}"
            try:
                result = zyte_request(url, api_key)
                if result.get("status") != "ok":
                    break
                jobs = result.get("jobs", [])
                if not jobs:
                    break
                all_jobs.extend(jobs)
                offset += len(jobs)
                if len(jobs) < 100:
                    break
            except Exception as e:
                print(f"  Error fetching {s} jobs: {e}")
                break
    return all_jobs


def fetch_item_count(api_key, project_id, job_id):
    url = f"https://app.zyte.com/api/jobs/{job_id}/items.json?project={project_id}&count=1"
    try:
        result = zyte_request(url, api_key)
        return result.get("total", 0)
    except Exception:
        return None


def classify_job(job):
    tags = job.get("tags", [])
    spider = job.get("spider", "")

    if spider == "zillow_detail":
        return "detail"

    for tag in tags:
        if "-rent-" in tag:
            return "rent"
        if "-sold-" in tag:
            return "sold"
        if "-sale-" in tag:
            return "sale"

    return "unknown"


def format_duration(seconds):
    if seconds is None:
        return "N/A"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def report_account(account, days=None, check_items=False):
    name = account["name"]
    api_key = account["api_key"]
    project_id = account["project_id"]

    if not api_key or not project_id:
        print(f"\n{'='*50}")
        print(f"  {name}: SKIPPED (no credentials)")
        print(f"{'='*50}")
        return None

    print(f"\n{'='*50}")
    print(f"  {name} (Project: {project_id})")
    print(f"{'='*50}")

    jobs = fetch_jobs(api_key, project_id)
    print(f"  Total jobs fetched: {len(jobs)}")

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        jobs = [
            j for j in jobs
            if j.get("started_time") and datetime.fromisoformat(j["started_time"].replace("Z", "+00:00")).replace(tzinfo=None) > cutoff
        ]
        print(f"  Jobs in last {days} days: {len(jobs)}")

    by_type = {"rent": 0, "sold": 0, "sale": 0, "detail": 0, "unknown": 0}
    by_state = {}
    empty_jobs = []
    total_items = 0
    jobs_with_items = 0
    jobs_checked = 0

    for job in jobs:
        job_type = classify_job(job)
        by_type[job_type] = by_type.get(job_type, 0) + 1

        state = job.get("state", "unknown")
        by_state[state] = by_state.get(state, 0) + 1

        if check_items and state == "finished":
            items = fetch_item_count(api_key, project_id, job.get("id"))
            jobs_checked += 1
            if items is not None:
                total_items += items
                if items > 0:
                    jobs_with_items += 1
                else:
                    empty_jobs.append({
                        "id": job.get("id"),
                        "type": job_type,
                        "tags": job.get("tags", []),
                        "started": job.get("started_time", ""),
                    })

    print(f"\n  By Type:")
    for jtype, count in sorted(by_type.items()):
        if count > 0:
            print(f"    {jtype:10s}: {count}")

    print(f"\n  By State:")
    for state, count in sorted(by_state.items()):
        print(f"    {state:10s}: {count}")

    if check_items:
        print(f"\n  Item Stats (checked {jobs_checked} finished jobs):")
        print(f"    Total items scraped : {total_items}")
        print(f"    Jobs with items     : {jobs_with_items}")
        print(f"    Jobs with 0 items   : {len(empty_jobs)}")

        if empty_jobs:
            print(f"\n  Empty Jobs (first 10):")
            for ej in empty_jobs[:10]:
                print(f"    {ej['id']} [{ej['type']}] {ej['tags'][:2]}")

    return {
        "name": name,
        "project_id": project_id,
        "total_jobs": len(jobs),
        "by_type": by_type,
        "by_state": by_state,
        "total_items": total_items,
        "jobs_with_items": jobs_with_items,
        "empty_jobs": len(empty_jobs) if check_items else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Zyte Scrapy Cloud job report")
    parser.add_argument("--days", type=int, help="Filter to last N days")
    parser.add_argument("--check-items", action="store_true", help="Check item counts for finished jobs (slower)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = []
    for account in ACCOUNTS:
        result = report_account(account, days=args.days, check_items=args.check_items)
        if result:
            results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"  SUMMARY")
        print(f"{'='*50}")
        total_jobs = sum(r["total_jobs"] for r in results)
        print(f"  Total jobs across all accounts: {total_jobs}")
        for r in results:
            print(f"\n  {r['name']}:")
            print(f"    Jobs: {r['total_jobs']}")
            for jtype, count in r["by_type"].items():
                if count > 0:
                    print(f"    {jtype}: {count}")


if __name__ == "__main__":
    main()
