#!/usr/bin/env python3
"""
Zyte Scrapy Cloud job report → Telegram.
Shows job stats, daily cost, and daily bandwidth per account.

Usage:
    python zyte_report.py              # Report for all accounts
    python zyte_report.py --days 7     # Last 7 days only
    python zyte_report.py --json       # Output as JSON
    python zyte_report.py --dry-run    # Don't send to Telegram

Env vars:
    ZYTE_ACCOUNTS='[{"name":"Acc1","api_key":"xxx","project_id":"123"}]'
    TELEGRAM_BOT_TOKEN='123:ABC'
    TELEGRAM_CHAT_ID='-100123'
"""

import json
import os
import sys
import base64
import argparse
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from dotenv import load_dotenv

# Load .env from jobs directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ZYTE_JOBS_URL = "https://app.zyte.com/api/jobs/list.json"
ZYTE_STATS_URL = "https://app.zyte.com/api/jobs/{job_id}/stats.json"

# Zyte pricing (per GB)
ZYTE_PRICING = {
    "datacenter": 0.00,
    "browser_api": 0.00,
    "proxy": 0.005,  # $5/GB
    "browser": 0.10,  # $100/GB
}


def load_accounts():
    raw = os.environ.get("ZYTE_ACCOUNTS", "")
    if raw:
        try:
            accounts = json.loads(raw)
            # Add name if missing
            for i, acc in enumerate(accounts):
                if "name" not in acc:
                    acc["name"] = f"Account {i + 1}"
            return accounts
        except json.JSONDecodeError as e:
            print(f"Error parsing ZYTE_ACCOUNTS: {e}")
            return []
    return [
        {
            "name": "Account 1",
            "api_key": os.environ.get("ZYTE_API_KEY", ""),
            "project_id": os.environ.get("ZYTE_PROJECT_ID", ""),
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


def fetch_job_stats(api_key, project_id, job_id):
    """Fetch stats for a single job.
    
    Zyte API returns stats in the job data itself:
    - items_scraped: number of items scraped
    - responses_received: number of responses received
    - elapsed: duration in milliseconds
    - errors_count: number of errors
    
    Bandwidth is estimated based on responses_received.
    """
    # The stats are already in the job data from fetch_jobs
    # This function is for additional stats if needed
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


def estimate_bandwidth(responses_received):
    """Estimate bandwidth based on responses received.
    
    Average web page response is ~100KB-500KB.
    Using 200KB as average for real estate sites.
    """
    avg_response_size = 200 * 1024  # 200KB
    return responses_received * avg_response_size


def calculate_cost_from_job(job):
    """Calculate cost from job data."""
    responses = job.get("responses_received", 0) or 0
    
    # Estimate bandwidth
    bandwidth_bytes = estimate_bandwidth(responses)
    bandwidth_gb = bandwidth_bytes / (1024 ** 3)
    
    # Calculate cost (proxy only for now)
    cost = bandwidth_gb * ZYTE_PRICING["proxy"]
    
    return cost, bandwidth_bytes


def report_account(account, days=None):
    name = account["name"]
    api_key = account["api_key"]
    project_id = account["project_id"]

    if not api_key or not project_id:
        return None

    jobs = fetch_jobs(api_key, project_id)

    if days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        jobs = [
            j for j in jobs
            if j.get("started_time") and datetime.fromisoformat(j["started_time"].replace("Z", "+00:00")).replace(tzinfo=None) > cutoff.replace(tzinfo=None)
        ]

    by_type = {"rent": 0, "sold": 0, "sale": 0, "detail": 0, "unknown": 0}
    by_state = {}
    daily_stats = {}  # date -> {bandwidth, cost, jobs}

    total_bandwidth = 0
    total_cost = 0.0
    total_items = 0

    for job in jobs:
        job_type = classify_job(job)
        by_type[job_type] = by_type.get(job_type, 0) + 1
        state = job.get("state", "unknown")
        by_state[state] = by_state.get(state, 0) + 1

        # Get job date
        started = job.get("started_time", "")
        if started:
            job_date = datetime.fromisoformat(started.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        else:
            job_date = "unknown"

        # Calculate cost and bandwidth for finished jobs
        if state == "finished":
            job_cost, job_bytes = calculate_cost_from_job(job)
            job_items = job.get("items_scraped", 0) or 0

            total_bandwidth += job_bytes
            total_cost += job_cost
            total_items += job_items

            # Aggregate by day
            if job_date not in daily_stats:
                daily_stats[job_date] = {"bandwidth": 0, "cost": 0.0, "jobs": 0, "items": 0}
            daily_stats[job_date]["bandwidth"] += job_bytes
            daily_stats[job_date]["cost"] += job_cost
            daily_stats[job_date]["jobs"] += 1
            daily_stats[job_date]["items"] += job_items

    return {
        "name": name,
        "project_id": project_id,
        "total_jobs": len(jobs),
        "by_type": by_type,
        "by_state": by_state,
        "total_bandwidth_bytes": total_bandwidth,
        "total_bandwidth_gb": round(total_bandwidth / (1024 ** 3), 4),
        "total_cost": round(total_cost, 4),
        "total_items": total_items,
        "daily": daily_stats,
    }


def format_size(bytes_val):
    """Format bytes to human readable."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.2f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_val / (1024 ** 3):.4f} GB"


def format_telegram_report(results, days=None):
    """Format report for Telegram."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 *Zyte Report* — {now}"]

    if days:
        lines[0] += f" _(last {days} days)_"

    total_jobs = 0
    total_bandwidth = 0
    total_cost = 0.0
    total_items = 0

    for r in results:
        total_jobs += r["total_jobs"]
        total_bandwidth += r["total_bandwidth_bytes"]
        total_cost += r["total_cost"]
        total_items += r["total_items"]

        lines.append(f"\n*{r['name']}* (Project: {r['project_id']})")
        lines.append(f"Jobs: {r['total_jobs']}")
        lines.append(f"Bandwidth: {format_size(r['total_bandwidth_bytes'])} ({r['total_bandwidth_gb']} GB)")
        lines.append(f"Cost: ${r['total_cost']:.4f}")
        lines.append(f"Items: {r['total_items']:,}")

        # Daily breakdown
        if r["daily"]:
            lines.append("\n_Daily Breakdown:_")
            for date in sorted(r["daily"].keys(), reverse=True)[:5]:
                d = r["daily"][date]
                lines.append(f"  {date}: {d['jobs']} jobs, {format_size(d['bandwidth'])}, ${d['cost']:.4f}")

    lines.append(f"\n*Total:*")
    lines.append(f"  Jobs: {total_jobs}")
    lines.append(f"  Bandwidth: {format_size(total_bandwidth)} ({total_bandwidth / (1024 ** 3):.4f} GB)")
    lines.append(f"  Cost: ${total_cost:.4f}")
    lines.append(f"  Items: {total_items:,}")

    return "\n".join(lines)


def send_telegram(text, bot_token=None, chat_id=None):
    """Send message to Telegram."""
    bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()

    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("✓ Telegram message sent")
                return True
            else:
                print(f"✗ Telegram error: {result}")
                return False
    except HTTPError as e:
        print(f"✗ Telegram error: {e.code} {e.read().decode()}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Zyte report → Telegram")
    parser.add_argument("--days", type=int, help="Filter to last N days")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to Telegram")
    parser.add_argument("--telegram-token", help="Override Telegram bot token")
    parser.add_argument("--telegram-chat", help="Override Telegram chat ID")
    args = parser.parse_args()

    accounts = load_accounts()
    if not accounts:
        print("No accounts configured in ZYTE_ACCOUNTS")
        sys.exit(1)

    results = []
    for account in accounts:
        result = report_account(account, days=args.days)
        if result:
            results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Print to console
        print(f"\n{'='*60}")
        print(f"  ZYTE REPORT")
        print(f"{'='*60}")

        total_jobs = 0
        total_bandwidth = 0
        total_cost = 0.0
        total_items = 0

        for r in results:
            total_jobs += r["total_jobs"]
            total_bandwidth += r["total_bandwidth_bytes"]
            total_cost += r["total_cost"]
            total_items += r["total_items"]

            print(f"\n  {r['name']} (Project: {r['project_id']})")
            print(f"  {'-'*50}")
            print(f"    Jobs:          {r['total_jobs']}")
            print(f"    Bandwidth:     {format_size(r['total_bandwidth_bytes'])} ({r['total_bandwidth_gb']} GB)")
            print(f"    Cost:          ${r['total_cost']:.4f}")
            print(f"    Items scraped: {r['total_items']:,}")

            print(f"\n    By Type:")
            for jtype, count in r["by_type"].items():
                if count > 0:
                    print(f"      {jtype:10s}: {count}")

            # Daily breakdown
            if r["daily"]:
                print(f"\n    Daily Breakdown:")
                for date in sorted(r["daily"].keys(), reverse=True)[:5]:
                    d = r["daily"][date]
                    print(f"      {date}: {d['jobs']} jobs, {format_size(d['bandwidth'])}, ${d['cost']:.4f}")

        print(f"\n  {'='*60}")
        print(f"  TOTALS")
        print(f"  {'='*60}")
        print(f"    Jobs:          {total_jobs}")
        print(f"    Bandwidth:     {format_size(total_bandwidth)} ({total_bandwidth / (1024 ** 3):.4f} GB)")
        print(f"    Cost:          ${total_cost:.4f}")
        print(f"    Items scraped: {total_items:,}")

    # Send to Telegram
    if not args.dry_run:
        telegram_text = format_telegram_report(results, days=args.days)
        send_telegram(
            telegram_text,
            bot_token=args.telegram_token,
            chat_id=args.telegram_chat,
        )


if __name__ == "__main__":
    main()
