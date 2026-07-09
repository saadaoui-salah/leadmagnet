#!/usr/bin/env python3
"""
Zyte Scrapy Cloud job report → Telegram.
Shows job stats per account and sends to Telegram bot.

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
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from dotenv import load_dotenv

# Load .env from jobs directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ZYTE_JOBS_URL = "https://app.zyte.com/api/jobs/list.json"

# Load accounts from env var
def load_accounts():
    raw = os.environ.get("ZYTE_ACCOUNTS", "")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Error parsing ZYTE_ACCOUNTS: {e}")
            return []
    # Fallback to individual env vars
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


def report_account(account, days=None):
    name = account["name"]
    api_key = account["api_key"]
    project_id = account["project_id"]

    if not api_key or not project_id:
        return None

    jobs = fetch_jobs(api_key, project_id)

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        jobs = [
            j for j in jobs
            if j.get("started_time") and datetime.fromisoformat(j["started_time"].replace("Z", "+00:00")).replace(tzinfo=None) > cutoff
        ]

    by_type = {"rent": 0, "sold": 0, "sale": 0, "detail": 0, "unknown": 0}
    by_state = {}

    for job in jobs:
        job_type = classify_job(job)
        by_type[job_type] = by_type.get(job_type, 0) + 1
        state = job.get("state", "unknown")
        by_state[state] = by_state.get(state, 0) + 1

    return {
        "name": name,
        "project_id": project_id,
        "total_jobs": len(jobs),
        "by_type": by_type,
        "by_state": by_state,
    }


def format_telegram_report(results, days=None):
    """Format report for Telegram."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 *Zyte Report* — {now}"]

    if days:
        lines[0] += f" _(last {days} days)_"

    total_jobs = 0
    for r in results:
        total_jobs += r["total_jobs"]
        lines.append(f"\n*{r['name']}* (Project: {r['project_id']})")
        lines.append(f"Jobs: {r['total_jobs']}")

        types = [f"{t}: {c}" for t, c in r["by_type"].items() if c > 0]
        if types:
            lines.append(f"Types: {', '.join(types)}")

        states = [f"{s}: {c}" for s, c in r["by_state"].items()]
        if states:
            lines.append(f"States: {', '.join(states)}")

    lines.append(f"\n*Total:* {total_jobs} jobs across {len(results)} accounts")

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
        print(f"\n{'='*50}")
        print(f"  ZYTE REPORT")
        print(f"{'='*50}")
        total_jobs = sum(r["total_jobs"] for r in results)
        for r in results:
            print(f"\n  {r['name']}:")
            print(f"    Jobs: {r['total_jobs']}")
            for jtype, count in r["by_type"].items():
                if count > 0:
                    print(f"    {jtype}: {count}")
        print(f"\n  Total: {total_jobs} jobs")

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
