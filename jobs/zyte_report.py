#!/usr/bin/env python3
"""
Daily scraping report → Telegram.
Zyte job stats + Webshare proxy stats (bandwidth, cost, requests, errors).

Usage:
    python zyte_report.py              # Report for all accounts
    python zyte_report.py --days 7     # Last 7 days only
    python zyte_report.py --json       # Output as JSON
    python zyte_report.py --dry-run    # Don't send to Telegram

Env vars:
    ZYTE_ACCOUNTS='[{"name":"Acc1","api_key":"xxx","project_id":"123"}]'
    WEBSHARE_API_TOKEN='your-token'
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
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load .env from jobs directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── API URLs ──────────────────────────────────────────────────────────────
ZYTE_JOBS_URL = "https://app.zyte.com/api/jobs/list.json"
WEBSHARE_BASE = "https://proxy.webshare.io/api/v2"
WEBSHARE_STATS_URL = f"{WEBSHARE_BASE}/stats/"
WEBSHARE_AGGREGATE_URL = f"{WEBSHARE_BASE}/stats/aggregate/"
WEBSHARE_PLAN_URL = f"{WEBSHARE_BASE}/subscription/plan/"

# Zyte pricing (per GB)
ZYTE_PRICING = {
    "datacenter": 0.00,
    "browser_api": 0.00,
    "proxy": 0.005,  # $5/GB
    "browser": 0.10,  # $100/GB
}


# ── Load Config ───────────────────────────────────────────────────────────
def load_accounts():
    raw = os.environ.get("ZYTE_ACCOUNTS", "")
    if raw:
        try:
            accounts = json.loads(raw)
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


def get_webshare_token():
    return os.environ.get("WEBSHARE_API_TOKEN", "")


# ── HTTP Helpers ──────────────────────────────────────────────────────────
def zyte_request(url, api_key):
    auth = base64.b64encode(f"{api_key}:".encode()).decode()
    req = Request(url, headers={"Authorization": f"Basic {auth}"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def webshare_request(url, token):
    req = Request(url, headers={"Authorization": f"Token {token}"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ── Zyte API ──────────────────────────────────────────────────────────────
def fetch_zyte_jobs(api_key, project_id, state=None):
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


def aggregate_zyte_stats(jobs, days=None):
    """Aggregate Zyte job stats."""
    by_type = {"rent": 0, "sold": 0, "sale": 0, "detail": 0, "unknown": 0}
    by_state = {}
    by_spider = {}
    daily_stats = {}

    total_items = 0
    total_responses = 0
    total_errors = 0
    total_elapsed_ms = 0

    error_jobs = []

    for job in jobs:
        # Filter by days
        if days:
            started = job.get("started_time", "")
            if started:
                job_dt = datetime.fromisoformat(started.replace("Z", "+00:00")).replace(tzinfo=None)
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                if job_dt < cutoff.replace(tzinfo=None):
                    continue

        job_type = classify_job(job)
        by_type[job_type] = by_type.get(job_type, 0) + 1

        state = job.get("state", "unknown")
        by_state[state] = by_state.get(state, 0) + 1

        spider = job.get("spider", "unknown")
        by_spider[spider] = by_spider.get(spider, 0) + 1

        # Get job date
        started = job.get("started_time", "")
        if started:
            job_date = datetime.fromisoformat(started.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        else:
            job_date = "unknown"

        # Accumulate stats
        items = job.get("items_scraped", 0) or 0
        responses = job.get("responses_received", 0) or 0
        errors = job.get("errors_count", 0) or 0
        elapsed = job.get("elapsed", 0) or 0

        total_items += items
        total_responses += responses
        total_errors += errors
        total_elapsed_ms += elapsed

        # Track error jobs
        if errors > 0 or state == "failed":
            error_jobs.append({
                "spider": spider,
                "state": state,
                "errors": errors,
                "items": items,
                "started": started,
            })

        # Aggregate by day
        if job_date not in daily_stats:
            daily_stats[job_date] = {
                "jobs": 0, "items": 0, "responses": 0, "errors": 0, "elapsed_ms": 0,
            }
        daily_stats[job_date]["jobs"] += 1
        daily_stats[job_date]["items"] += items
        daily_stats[job_date]["responses"] += responses
        daily_stats[job_date]["errors"] += errors
        daily_stats[job_date]["elapsed_ms"] += elapsed

    return {
        "total_jobs": len(jobs),
        "by_type": by_type,
        "by_state": by_state,
        "by_spider": by_spider,
        "total_items": total_items,
        "total_responses": total_responses,
        "total_errors": total_errors,
        "total_elapsed_ms": total_elapsed_ms,
        "error_jobs": error_jobs[:10],  # top 10 error jobs
        "daily": daily_stats,
    }


# ── Webshare API ──────────────────────────────────────────────────────────
def fetch_webshare_plans(token):
    """Fetch all plans (active + cancelled) to get pricing info."""
    try:
        result = webshare_request(WEBSHARE_PLAN_URL, token)
        return result.get("results", [])
    except Exception as e:
        print(f"  Error fetching Webshare plans: {e}")
        return []


def fetch_webshare_stats(token, timestamp_gte, timestamp_lte, plan_id=None):
    """Fetch hourly stats from Webshare."""
    params = {
        "timestamp__gte": timestamp_gte,
        "timestamp__lte": timestamp_lte,
    }
    if plan_id:
        params["plan_id"] = plan_id

    url = f"{WEBSHARE_STATS_URL}?{urlencode(params)}"
    try:
        return webshare_request(url, token)
    except Exception as e:
        print(f"  Error fetching Webshare stats: {e}")
        return []


def fetch_webshare_aggregate(token, timestamp_gte, timestamp_lte, plan_id=None):
    """Fetch aggregate stats from Webshare."""
    params = {
        "timestamp__gte": timestamp_gte,
        "timestamp__lte": timestamp_lte,
    }
    if plan_id:
        params["plan_id"] = plan_id

    url = f"{WEBSHARE_AGGREGATE_URL}?{urlencode(params)}"
    try:
        return webshare_request(url, token)
    except Exception as e:
        print(f"  Error fetching Webshare aggregate: {e}")
        return {}


def aggregate_webshare_stats(token, days=1):
    """Fetch and aggregate Webshare proxy stats."""
    now = datetime.now(timezone.utc)
    gte = (now - timedelta(days=days)).isoformat()
    lte = now.isoformat()

    # Fetch plans
    plans = fetch_webshare_plans(token)
    active_plans = [p for p in plans if p.get("status") == "active"]

    plan_info = {}
    for plan in active_plans:
        plan_info[plan["id"]] = {
            "monthly_price": plan.get("monthly_price", 0),
            "bandwidth_limit": plan.get("bandwidth_limit", 0),
            "proxy_type": plan.get("proxy_type", "unknown"),
            "proxy_subtype": plan.get("proxy_subtype", "unknown"),
            "proxy_count": plan.get("proxy_count", 0),
        }

    # Fetch hourly stats (for daily breakdown)
    hourly_stats = fetch_webshare_stats(token, gte, lte)

    # Fetch aggregate stats
    aggregate = fetch_webshare_aggregate(token, gte, lte)

    # Calculate cost from plan pricing
    # Webshare charges per proxy per month, not per GB
    total_monthly_cost = sum(p.get("monthly_price", 0) for p in active_plans)
    # Prorate to days
    daily_cost = total_monthly_cost / 30.0 if total_monthly_cost > 0 else 0
    period_cost = daily_cost * days

    # Build daily breakdown from hourly stats
    daily_breakdown = {}
    for stat in hourly_stats:
        ts = stat.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                day = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        else:
            continue

        if day not in daily_breakdown:
            daily_breakdown[day] = {
                "bandwidth_bytes": 0,
                "requests": 0,
                "requests_successful": 0,
                "requests_failed": 0,
                "error_reasons": [],
                "proxies_used": 0,
            }

        d = daily_breakdown[day]
        d["bandwidth_bytes"] += stat.get("bandwidth_total", 0)
        d["requests"] += stat.get("requests_total", 0)
        d["requests_successful"] += stat.get("requests_successful", 0)
        d["requests_failed"] += stat.get("requests_failed", 0)
        d["proxies_used"] = max(d["proxies_used"], stat.get("number_of_proxies_used", 0))

        # Collect error reasons
        for err in stat.get("error_reasons", []):
            d["error_reasons"].append(err)

    # Merge error reasons per day
    for day, d in daily_breakdown.items():
        merged = {}
        for err in d["error_reasons"]:
            reason = err.get("reason", "unknown")
            merged[reason] = merged.get(reason, 0) + err.get("count", 0)
        d["error_reasons"] = [{"reason": k, "count": v} for k, v in merged.items()]

    return {
        "plans": plan_info,
        "aggregate": {
            "bandwidth_bytes": aggregate.get("bandwidth_total", 0),
            "bandwidth_projected": aggregate.get("bandwidth_projected", 0),
            "requests": aggregate.get("requests_total", 0),
            "requests_successful": aggregate.get("requests_successful", 0),
            "requests_failed": aggregate.get("requests_failed", 0),
            "error_reasons": aggregate.get("error_reasons", []),
            "proxies_used": aggregate.get("number_of_proxies_used", 0),
            "protocols_used": aggregate.get("protocols_used", {}),
        },
        "cost": {
            "monthly": total_monthly_cost,
            "daily": round(daily_cost, 4),
            "period": round(period_cost, 4),
        },
        "daily": daily_breakdown,
    }


# ── Format Report (4 messages) ────────────────────────────────────────────
def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.2f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_val / (1024 ** 3):.4f} GB"


def format_duration(ms):
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        return f"{ms / 60000:.1f}min"


def format_scheduled_jobs(zyte_stats, days=None):
    """Message 1: Jobs scheduled."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📋 *Scheduled Jobs* — {now}"]

    by_state = zyte_stats.get("by_state", {})
    pending = by_state.get("pending", 0)
    running = by_state.get("running", 0)

    lines.append(f"Pending: {pending}")
    lines.append(f"Running: {running}")

    if zyte_stats.get("by_spider"):
        lines.append("\n_By spider:_")
        for spider, count in sorted(zyte_stats["by_spider"].items(), key=lambda x: -x[1]):
            lines.append(f"  {spider}: {count}")

    return "\n".join(lines)


def format_job_summary(zyte_stats, days=None):
    """Message 2: Jobs finished + items + errors."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 *Job Summary* — {now}"]

    by_state = zyte_stats.get("by_state", {})
    finished = by_state.get("finished", 0)
    failed = by_state.get("failed", 0)
    total = zyte_stats.get("total_jobs", 0)
    remaining = total - finished

    lines.append(f"Finished: {finished}")
    lines.append(f"Failed: {failed}")
    lines.append(f"Remaining: {remaining}")
    lines.append(f"Items scraped: {zyte_stats.get('total_items', 0):,}")
    lines.append(f"Errors: {zyte_stats.get('total_errors', 0):,}")
    lines.append(f"Runtime: {format_duration(zyte_stats.get('total_elapsed_ms', 0))}")

    if zyte_stats.get("error_jobs"):
        lines.append(f"\n⚠️ *Error jobs:* {len(zyte_stats['error_jobs'])}")
        for ej in zyte_stats["error_jobs"][:5]:
            lines.append(f"  {ej['spider']} — {ej['errors']} errors ({ej['state']})")

    return "\n".join(lines)


def format_webshare_cost(webshare_stats, days=None):
    """Message 3: Webshare proxy cost."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"💰 *Webshare Proxy Cost* — {now}"]

    plans = webshare_stats.get("plans", {})
    if plans:
        for pid, pinfo in plans.items():
            lines.append(f"Plan: {pinfo['proxy_type']}/{pinfo['proxy_subtype']} ({pinfo['proxy_count']} proxies)")
            lines.append(f"Monthly: ${pinfo['monthly_price']:.2f}")
            if pinfo["bandwidth_limit"] > 0:
                lines.append(f"Bandwidth limit: {pinfo['bandwidth_limit']:.1f} GB")

    cost = webshare_stats.get("cost", {})
    if cost:
        lines.append(f"\nCost ({days or 1}d): ${cost.get('period', 0):.2f}")
        lines.append(f"Daily: ${cost.get('daily', 0):.4f}")

    agg = webshare_stats.get("aggregate", {})
    if agg:
        bw = agg.get("bandwidth_bytes", 0)
        lines.append(f"\nBandwidth: {format_size(bw)} ({bw / (1024**3):.4f} GB)")
        lines.append(f"Requests: {agg.get('requests', 0):,}")
        lines.append(f"  Successful: {agg.get('requests_successful', 0):,}")
        lines.append(f"  Failed: {agg.get('requests_failed', 0):,}")

        if agg.get("error_reasons"):
            lines.append(f"\n⚠️ *Proxy errors:*")
            for err in agg["error_reasons"][:5]:
                lines.append(f"  {err['reason']}: {err['count']}")

    return "\n".join(lines)


def format_daily_breakdown(zyte_stats, webshare_stats, days=None):
    """Message 4: Daily breakdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"📅 *Daily Breakdown* — {now}"]

    all_dates = set(list(zyte_stats.get("daily", {}).keys()) + list(webshare_stats.get("daily", {}).keys()))
    if all_dates:
        for date in sorted(all_dates, reverse=True)[:7]:
            z = zyte_stats.get("daily", {}).get(date, {})
            w = webshare_stats.get("daily", {}).get(date, {})
            bw = w.get("bandwidth_bytes", 0)
            lines.append(
                f"*{date}*: "
                f"{z.get('jobs', 0)} jobs, "
                f"{z.get('items', 0)} items, "
                f"{format_size(bw)}, "
                f"{z.get('errors', 0) + w.get('requests_failed', 0)} errors"
            )
    else:
        lines.append("No data available.")

    return "\n".join(lines)


# ── Telegram ──────────────────────────────────────────────────────────────
def send_telegram(text, bot_token=None, chat_id=None):
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


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Daily scraping report → Telegram")
    parser.add_argument("--days", type=int, default=1, help="Report period in days (default: 1)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to Telegram")
    parser.add_argument("--telegram-token", help="Override Telegram bot token")
    parser.add_argument("--telegram-chat", help="Override Telegram chat ID")
    args = parser.parse_args()

    webshare_token = get_webshare_token()
    accounts = load_accounts()

    if not accounts and not webshare_token:
        print("No accounts configured (ZYTE_ACCOUNTS or WEBSHARE_API_TOKEN)")
        sys.exit(1)

    # ── Fetch Zyte stats ──────────────────────────────────────────────
    all_jobs = []
    for account in accounts:
        api_key = account.get("api_key", "")
        project_id = account.get("project_id", "")
        if api_key and project_id:
            print(f"Fetching Zyte jobs for {account['name']}...")
            jobs = fetch_zyte_jobs(api_key, project_id)
            all_jobs.extend(jobs)

    zyte_stats = aggregate_zyte_stats(all_jobs, days=args.days)

    # ── Fetch Webshare stats ──────────────────────────────────────────
    webshare_stats = {"plans": {}, "aggregate": {}, "cost": {}, "daily": {}}
    if webshare_token:
        print("Fetching Webshare proxy stats...")
        webshare_stats = aggregate_webshare_stats(webshare_token, days=args.days)

    # ── Output ────────────────────────────────────────────────────────
    if args.json:
        output = {
            "zyte": zyte_stats,
            "webshare": webshare_stats,
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        # Console output
        print(f"\n{'='*60}")
        print(f"  DAILY SCRAPING REPORT")
        print(f"{'='*60}")

        print(f"\n  ZYTE JOBS")
        print(f"  {'-'*50}")
        print(f"    Total jobs:     {zyte_stats['total_jobs']}")
        print(f"    Items scraped:  {zyte_stats['total_items']:,}")
        print(f"    Responses:      {zyte_stats['total_responses']:,}")
        print(f"    Errors:         {zyte_stats['total_errors']:,}")
        print(f"    Runtime:        {format_duration(zyte_stats['total_elapsed_ms'])}")

        if zyte_stats["by_spider"]:
            print(f"\n    By spider:")
            for spider, count in sorted(zyte_stats["by_spider"].items(), key=lambda x: -x[1]):
                print(f"      {spider:30s} {count}")

        print(f"\n  WEBSHARE PROXY")
        print(f"  {'-'*50}")

        if webshare_stats["plans"]:
            for pid, pinfo in webshare_stats["plans"].items():
                print(f"    Plan: {pinfo['proxy_type']}/{pinfo['proxy_subtype']} ({pinfo['proxy_count']} proxies)")
                print(f"    Monthly cost: ${pinfo['monthly_price']:.2f}")
                if pinfo["bandwidth_limit"] > 0:
                    print(f"    Bandwidth limit: {pinfo['bandwidth_limit']:.1f} GB")

        agg = webshare_stats.get("aggregate", {})
        if agg:
            bw = agg.get("bandwidth_bytes", 0)
            print(f"\n    Bandwidth:    {format_size(bw)} ({bw / (1024**3):.4f} GB)")
            print(f"    Requests:     {agg.get('requests', 0):,}")
            print(f"      Successful: {agg.get('requests_successful', 0):,}")
            print(f"      Failed:     {agg.get('requests_failed', 0):,}")
            print(f"    Proxies used: {agg.get('proxies_used', 0)}")

            if agg.get("error_reasons"):
                print(f"\n    Proxy errors:")
                for err in agg["error_reasons"][:5]:
                    print(f"      {err['reason']}: {err['count']}")

        cost = webshare_stats.get("cost", {})
        if cost:
            print(f"\n    Cost ({args.days}d):  ${cost.get('period', 0):.2f}")
            print(f"    Monthly:    ${cost.get('monthly', 0):.2f}")
            print(f"    Daily:      ${cost.get('daily', 0):.4f}")

        # Daily breakdown
        all_dates = set(list(zyte_stats["daily"].keys()) + list(webshare_stats.get("daily", {}).keys()))
        if all_dates:
            print(f"\n  DAILY BREAKDOWN")
            print(f"  {'-'*50}")
            for date in sorted(all_dates, reverse=True)[:7]:
                z = zyte_stats["daily"].get(date, {})
                w = webshare_stats.get("daily", {}).get(date, {})
                bw = w.get("bandwidth_bytes", 0)
                print(f"    {date}: {z.get('jobs', 0)} jobs, {z.get('items', 0)} items, {format_size(bw)}, {z.get('errors', 0)} errors")

        print(f"\n{'='*60}")

    # ── Send to Telegram (4 messages) ────────────────────────────────
    if not args.dry_run:
        msg1 = format_scheduled_jobs(zyte_stats, days=args.days)
        msg2 = format_job_summary(zyte_stats, days=args.days)
        msg3 = format_webshare_cost(webshare_stats, days=args.days)
        msg4 = format_daily_breakdown(zyte_stats, webshare_stats, days=args.days)

        for i, msg in enumerate([msg1, msg2, msg3, msg4], 1):
            send_telegram(
                msg,
                bot_token=args.telegram_token,
                chat_id=args.telegram_chat,
            )


if __name__ == "__main__":
    main()
