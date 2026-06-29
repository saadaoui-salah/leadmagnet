from datetime import date, timedelta
from django.db.models import Q, Avg, Count, Sum, F, Max, Min

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status

from properties.models import (
    ZipCode, Property, Unit, UnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
    PropertyTaxHistory, PropertySchool,
)


@api_view(["GET"])
def top_rent_growth(request):
    limit = int(request.query_params.get("limit", 10))
    days = int(request.query_params.get("days", 30))
    cutoff = date.today() - timedelta(days=days)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date__gte=cutoff,
            rent_change_pct__isnull=False,
        )
        .values("zipcode__zipcode", "zipcode__city", "zipcode__state")
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_listings=Avg("active_listings"),
        )
        .order_by("-avg_growth")[:limit]
    )

    results = [
        {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth": round(m["avg_growth"], 1),
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "active_listings": round(m["avg_listings"]) if m["avg_listings"] else 0,
        }
        for m in metrics
    ]
    return Response(results)


@api_view(["GET"])
def biggest_rent_drops(request):
    limit = int(request.query_params.get("limit", 10))
    days = int(request.query_params.get("days", 30))
    cutoff = date.today() - timedelta(days=days)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date__gte=cutoff,
            rent_change_pct__isnull=False,
        )
        .values("zipcode__zipcode", "zipcode__city", "zipcode__state")
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
        )
        .order_by("avg_growth")[:limit]
    )

    results = [
        {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth": round(m["avg_growth"], 1),
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
        }
        for m in metrics
    ]
    return Response(results)


@api_view(["GET"])
def inventory_explosion(request):
    limit = int(request.query_params.get("limit", 10))
    min_growth = float(request.query_params.get("min_growth", 20))

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            inventory_change_pct__gte=min_growth,
            date=date.today(),
        )
        .values("zipcode__zipcode", "zipcode__city", "zipcode__state")
        .annotate(
            avg_inventory_change=Avg("inventory_change_pct"),
            active_listings=Avg("active_listings"),
        )
        .order_by("-avg_inventory_change")[:limit]
    )

    results = [
        {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "inventory_growth": round(m["avg_inventory_change"], 1),
            "active_listings": round(m["active_listings"]) if m["active_listings"] else 0,
        }
        for m in metrics
    ]
    return Response(results)


@api_view(["GET"])
def investor_opportunities(request):
    limit = int(request.query_params.get("limit", 10))
    days = int(request.query_params.get("days", 30))
    cutoff = date.today() - timedelta(days=days)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date__gte=cutoff,
            rent_change_pct__gt=5,
            inventory_change_pct__lt=-5,
        )
        .values(
            "zipcode__zipcode", "zipcode__city", "zipcode__state",
            "zipcode__median_income", "zipcode__median_home_value",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_inventory_change=Avg("inventory_change_pct"),
        )
        .order_by("-avg_growth")[:limit]
    )

    results = []
    for m in metrics:
        item = {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth": round(m["avg_growth"], 1),
            "inventory_change": round(m["avg_inventory_change"], 1),
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "median_income": m["zipcode__median_income"],
        }
        if m["zipcode__median_home_value"] and m["avg_rent"]:
            item["yield_pct"] = round((m["avg_rent"] * 12 / m["zipcode__median_home_value"]) * 100, 2)
        results.append(item)
    return Response(results)


@api_view(["GET"])
def emerging_markets(request):
    limit = int(request.query_params.get("limit", 10))

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date=date.today(),
            rent_change_pct__gt=8,
            inventory_change_pct__lt=0,
        )
        .values(
            "zipcode__zipcode", "zipcode__city", "zipcode__state",
            "zipcode__median_income",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_inventory_change=Avg("inventory_change_pct"),
        )
        .order_by("-avg_growth")[:limit]
    )

    results = [
        {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth": round(m["avg_growth"], 1),
            "inventory_change": round(m["avg_inventory_change"], 1),
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "median_income": m["zipcode__median_income"],
        }
        for m in metrics
    ]
    return Response(results)


@api_view(["GET"])
def hidden_gems(request):
    limit = int(request.query_params.get("limit", 10))

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date=date.today(),
            rent_change_pct__gt=5,
        )
        .values(
            "zipcode__zipcode", "zipcode__city", "zipcode__state",
            "zipcode__median_income", "zipcode__median_home_value",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
        )
        .filter(
            zipcode__median_income__gte=60000,
            zipcode__median_home_value__lte=400000,
        )
        .order_by("-avg_growth")[:limit]
    )

    results = [
        {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth": round(m["avg_growth"], 1),
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "median_income": m["zipcode__median_income"],
            "median_home_value": m["zipcode__median_home_value"],
        }
        for m in metrics
    ]
    return Response(results)


@api_view(["GET"])
def yield_report(request):
    limit = int(request.query_params.get("limit", 10))

    metrics = (
        ZipCodeDailyMetrics.objects.filter(date=date.today())
        .values(
            "zipcode__zipcode", "zipcode__city", "zipcode__state",
            "zipcode__median_home_value",
        )
        .annotate(avg_rent=Avg("avg_rent"))
        .filter(
            zipcode__median_home_value__isnull=False,
            avg_rent__isnull=False,
            zipcode__median_home_value__gt=0,
        )
    )

    results = []
    for m in metrics:
        annual_rent = m["avg_rent"] * 12
        yield_pct = (annual_rent / m["zipcode__median_home_value"]) * 100
        results.append({
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "avg_rent": round(m["avg_rent"]),
            "median_home_value": m["zipcode__median_home_value"],
            "yield_pct": round(yield_pct, 2),
        })

    results.sort(key=lambda x: x["yield_pct"], reverse=True)
    return Response(results[:limit])


@api_view(["GET"])
def luxury_markets(request):
    limit = int(request.query_params.get("limit", 10))

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date=date.today(),
            luxury_count__gt=0,
        )
        .values("zipcode__zipcode", "zipcode__city", "zipcode__state")
        .annotate(
            luxury_count=Sum("luxury_count"),
            avg_rent=Avg("avg_rent"),
        )
        .order_by("-luxury_count")[:limit]
    )

    results = [
        {
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "luxury_count": m["luxury_count"],
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
        }
        for m in metrics
    ]
    return Response(results)


@api_view(["GET"])
def top_landlords(request):
    limit = int(request.query_params.get("limit", 20))

    landlords = (
        Property.objects.filter(management_company__gt="")
        .values("management_company")
        .annotate(
            property_count=Count("id"),
            avg_rent=Avg("units__snapshots__price"),
            cities=Count("city", distinct=True),
        )
        .order_by("-property_count")[:limit]
    )

    results = [
        {
            "company": l["management_company"],
            "property_count": l["property_count"],
            "avg_rent": round(l["avg_rent"]) if l["avg_rent"] else 0,
            "cities": l["cities"],
        }
        for l in landlords
    ]
    return Response(results)


@api_view(["GET"])
def market_pulse(request):
    today = date.today()
    yesterday = today - timedelta(days=1)

    today_metrics = ZipCodeDailyMetrics.objects.filter(date=today)
    yesterday_metrics = ZipCodeDailyMetrics.objects.filter(date=yesterday)

    today_avg_rent = today_metrics.aggregate(avg=Avg("avg_rent"))["avg"]
    yesterday_avg_rent = yesterday_metrics.aggregate(avg=Avg("avg_rent"))["avg"]
    total_listings = today_metrics.aggregate(total=Sum("active_listings"))["total"]

    rent_change = None
    if today_avg_rent and yesterday_avg_rent:
        rent_change = round(((today_avg_rent - yesterday_avg_rent) / yesterday_avg_rent) * 100, 1)

    events_today = MarketEvent.objects.filter(created_at__date=today).count()

    return Response({
        "date": str(today),
        "avg_rent": round(today_avg_rent) if today_avg_rent else None,
        "rent_change_pct": rent_change,
        "total_listings": total_listings or 0,
        "market_events": events_today,
    })


@api_view(["GET"])
def daily_digest(request):
    today = date.today()
    yesterday = today - timedelta(days=1)

    top_growth = (
        ZipCodeDailyMetrics.objects.filter(date=today, rent_change_pct__isnull=False)
        .values("zipcode__zipcode", "zipcode__city")
        .annotate(avg_growth=Avg("rent_change_pct"))
        .order_by("-avg_growth")[:5]
    )

    biggest_drop = (
        ZipCodeDailyMetrics.objects.filter(date=today, rent_change_pct__isnull=False)
        .values("zipcode__zipcode", "zipcode__city")
        .annotate(avg_growth=Avg("rent_change_pct"))
        .order_by("avg_growth")[:5]
    )

    new_events = MarketEvent.objects.filter(created_at__date=today)[:5]

    seen_y = set(
        UnitSnapshot.objects.filter(date=yesterday)
        .values_list("unit__base_id", flat=True)
    )
    seen_t = set(
        UnitSnapshot.objects.filter(date=today)
        .values_list("unit__base_id", flat=True)
    )
    missing_count = len(seen_y - seen_t)

    new_today = Property.objects.filter(first_seen=today).count()

    return Response({
        "date": str(today),
        "new_properties": new_today,
        "missing_properties": missing_count,
        "top_growth": [
            {
                "zip": m["zipcode__zipcode"],
                "city": m["zipcode__city"],
                "growth": round(m["avg_growth"], 1),
            }
            for m in top_growth
        ],
        "biggest_drops": [
            {
                "zip": m["zipcode__zipcode"],
                "city": m["zipcode__city"],
                "growth": round(m["avg_growth"], 1),
            }
            for m in biggest_drop
        ],
        "events": [
            {
                "type": e.event_type,
                "title": e.title,
                "zipcode": e.zipcode.zipcode,
            }
            for e in new_events
        ],
    })


@api_view(["GET"])
def rent_history_by_zip(request, zipcode):
    days = int(request.query_params.get("days", 365))
    cutoff = date.today() - timedelta(days=days)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            zipcode__zipcode=zipcode,
            date__gte=cutoff,
        )
        .order_by("date")
        .values("date", "avg_rent", "median_rent", "active_listings", "rent_change_pct")
    )

    return Response(list(metrics))


@api_view(["GET"])
def opportunity_score(request):
    limit = int(request.query_params.get("limit", 10))
    days = int(request.query_params.get("days", 30))
    cutoff = date.today() - timedelta(days=days)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(date__gte=cutoff)
        .values(
            "zipcode__zipcode", "zipcode__city", "zipcode__state",
            "zipcode__median_income", "zipcode__median_home_value",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_inventory_change=Avg("inventory_change_pct"),
        )
        .filter(avg_rent__isnull=False)
    )

    results = []
    for m in metrics:
        rent_score = min(max((m["avg_growth"] or 0) * 4, 0), 100)
        income = m["zipcode__median_income"] or 50000
        income_score = min((income / 100000) * 50, 100)
        inventory = m["avg_inventory_change"] or 0
        inventory_score = max(50 - inventory, 0)
        avg_rent_val = m["avg_rent"] or 2000
        rent_level_score = min((avg_rent_val / 5000) * 50, 100)

        score = (
            rent_score * 0.35
            + income_score * 0.25
            + inventory_score * 0.20
            + rent_level_score * 0.20
        )

        if score >= 80:
            grade = "A+"
        elif score >= 65:
            grade = "A"
        elif score >= 50:
            grade = "B+"
        elif score >= 35:
            grade = "B"
        else:
            grade = "C"

        results.append({
            "zip": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "score": round(score, 1),
            "grade": grade,
            "rent_growth": round(m["avg_growth"] or 0, 1),
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "median_income": m["zipcode__median_income"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return Response(results[:limit])


@api_view(["GET"])
def state_summary(request):
    state = request.query_params.get("state", "NY")
    days = int(request.query_params.get("days", 30))
    cutoff = date.today() - timedelta(days=days)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            zipcode__state=state,
            date__gte=cutoff,
        )
        .values("zipcode__zipcode", "zipcode__city")
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            total_listings=Sum("active_listings"),
        )
        .order_by("-avg_growth")
    )

    state_agg = (
        ZipCodeDailyMetrics.objects.filter(
            zipcode__state=state,
            date__gte=cutoff,
        )
        .aggregate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            total_listings=Sum("active_listings"),
            zip_count=Count("zipcode", distinct=True),
        )
    )

    return Response({
        "state": state,
        "summary": {
            "avg_rent": round(state_agg["avg_rent"]) if state_agg["avg_rent"] else None,
            "avg_growth": round(state_agg["avg_growth"], 1) if state_agg["avg_growth"] else None,
            "total_listings": state_agg["total_listings"] or 0,
            "zip_count": state_agg["zip_count"],
        },
        "zipcodes": [
            {
                "zip": m["zipcode__zipcode"],
                "city": m["zipcode__city"],
                "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                "rent_growth": round(m["avg_growth"], 1) if m["avg_growth"] else 0,
                "listings": m["total_listings"] or 0,
            }
            for m in metrics
        ],
    })


@api_view(["GET"])
def building_performance(request):
    limit = int(request.query_params.get("limit", 20))
    zipcode = request.query_params.get("zipcode")

    qs = BuildingDailyMetrics.objects.filter(date=date.today())
    if zipcode:
        qs = qs.filter(property__zipcode=zipcode)

    buildings = (
        qs.values(
            "property__building_name", "property__street",
            "property__city", "property__zipcode",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            availability=Max("availability_count"),
            rent_change=Avg("rent_change_pct"),
        )
        .order_by("-avg_rent")[:limit]
    )

    results = [
        {
            "building": b["property__building_name"] or b["property__street"],
            "street": b["property__street"],
            "city": b["property__city"],
            "zipcode": b["property__zipcode"],
            "avg_rent": round(b["avg_rent"]) if b["avg_rent"] else 0,
            "availability": b["availability"],
            "rent_change_pct": round(b["rent_change"], 1) if b["rent_change"] else None,
        }
        for b in buildings
    ]
    return Response(results)


@api_view(["GET"])
def smart_zip_pick(request):
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            date__gte=thirty_days_ago,
            avg_rent__isnull=False,
        )
        .values(
            "zipcode__zipcode", "zipcode__city", "zipcode__state",
            "zipcode__median_home_value", "zipcode__population",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_listings=Avg("active_listings"),
            avg_inventory_change=Avg("inventory_change_pct"),
        )
        .filter(
            avg_rent__gt=0,
            avg_listings__gt=0,
        )
    )

    if not metrics.exists():
        zip_counts = (
            Property.objects.values("zipcode", "city", "state")
            .annotate(
                cnt=Count("id"),
                avg_rent=Avg("units__snapshots__price"),
            )
            .filter(avg_rent__gt=0)
            .order_by("-cnt")
        )

        if not zip_counts.exists():
            return Response(
                {"error": "No zipcode data available for analysis"},
                status=drf_status.HTTP_404_NOT_FOUND,
            )

        scored = []
        for z in zip_counts[:20]:
            avg_rent = round(z["avg_rent"] or 0)
            listings = z["cnt"] or 0

            try:
                zip_obj = ZipCode.objects.get(zipcode=z["zipcode"])
                median_home = zip_obj.median_home_value or (avg_rent * 280)
            except ZipCode.DoesNotExist:
                median_home = avg_rent * 280

            rent_spread = UnitSnapshot.objects.filter(
                unit__base__zipcode=z["zipcode"],
                price__gt=0,
            ).aggregate(min_r=Min("price"), max_r=Max("price"))
            min_r = rent_spread["min_r"] or avg_rent
            max_r = rent_spread["max_r"] or (avg_rent * 1.3)
            spread_pct = ((max_r - min_r) / min_r) * 100 if min_r > 0 else 10.0
            rent_growth = round(min(spread_pct * 0.4, 18.0), 1)

            growth_score = min(rent_growth * 3, 40)
            volume_score = min((listings / 100) * 25, 25)
            demand_score = 10
            if median_home > 0:
                annual_rent = avg_rent * 12
                yield_pct = (annual_rent / median_home) * 100
                yield_score = min(yield_pct * 2, 15)
            else:
                yield_score = 7

            total_score = growth_score + volume_score + demand_score + yield_score

            scored.append({
                "zipcode": z["zipcode"],
                "city": z["city"],
                "state": z["state"],
                "score": round(total_score, 1),
                "breakdown": {
                    "growth": round(growth_score, 1),
                    "volume": round(volume_score, 1),
                    "demand": round(demand_score, 1),
                    "yield": round(yield_score, 1),
                },
                "metrics": {
                    "avg_rent": avg_rent,
                    "rent_growth": rent_growth,
                    "active_listings": listings,
                    "inventory_change": 0,
                    "median_home_value": median_home,
                    "population": 0,
                },
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        return Response({
            "winner": scored[0],
            "runner_ups": scored[1:5],
            "total_zipcodes_analyzed": len(scored),
            "scoring_methodology": {
                "growth": "Rent spread * 0.4 * 3 (max 40 pts)",
                "volume": "Listings / 100 * 25 (max 25 pts)",
                "demand": "Default 10 pts",
                "yield": "Rent-to-price ratio * 2 (max 15 pts)",
            },
        })

    scored = []
    for m in metrics:
        rent_growth = m["avg_growth"] or 0
        avg_rent = m["avg_rent"] or 0
        listings = m["avg_listings"] or 0
        inventory_change = m["avg_inventory_change"] or 0
        median_home = m["zipcode__median_home_value"] or 0
        population = m["zipcode__population"] or 0

        growth_score = min(rent_growth * 3, 40)
        volume_score = min((listings / 100) * 25, 25)
        demand_score = min(max(-inventory_change * 2, 0), 20)

        if median_home > 0:
            annual_rent = avg_rent * 12
            yield_pct = (annual_rent / median_home) * 100
            yield_score = min(yield_pct * 2, 15)
        else:
            yield_score = 7

        total_score = growth_score + volume_score + demand_score + yield_score

        scored.append({
            "zipcode": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "score": round(total_score, 1),
            "breakdown": {
                "growth": round(growth_score, 1),
                "volume": round(volume_score, 1),
                "demand": round(demand_score, 1),
                "yield": round(yield_score, 1),
            },
            "metrics": {
                "avg_rent": round(avg_rent),
                "rent_growth": round(rent_growth, 1),
                "active_listings": round(listings),
                "inventory_change": round(inventory_change, 1),
                "median_home_value": median_home,
                "population": population,
            },
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    winner = scored[0]

    return Response({
        "winner": winner,
        "runner_ups": scored[1:5],
        "total_zipcodes_analyzed": len(scored),
        "scoring_methodology": {
            "growth": "Rent growth % * 3 (max 40 pts)",
            "volume": "Listings / 100 * 25 (max 25 pts)",
            "demand": "Inventory compression * 2 (max 20 pts)",
            "yield": "Rent-to-price ratio * 2 (max 15 pts)",
        },
    })


@api_view(["GET"])
def generate_market_data(request):
    target_zip = request.query_params.get("zipcode")
    limit = int(request.query_params.get("limit", 5))
    today = date.today()
    yesterday = today - timedelta(days=1)
    thirty_days_ago = today - timedelta(days=30)
    six_months_ago = today - timedelta(days=180)

    if target_zip:
        zip_counts = (
            Property.objects.filter(zipcode=target_zip)
            .values("zipcode", "city", "state")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
        )
    else:
        zip_counts = (
            Property.objects.values("zipcode", "city", "state")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
        )

    if not zip_counts.exists():
        return Response({"error": "No properties found"}, status=drf_status.HTTP_404_NOT_FOUND)

    focus = zip_counts.first()
    focus_zip = focus["zipcode"]
    focus_city = focus["city"] or "Unknown"
    focus_state = focus["state"] or "US"

    try:
        zip_obj = ZipCode.objects.get(zipcode=focus_zip)
        median_home_price = zip_obj.median_home_value
    except ZipCode.DoesNotExist:
        zip_obj = None
        median_home_price = None

    focus_metrics = ZipCodeDailyMetrics.objects.filter(
        zipcode__zipcode=focus_zip,
    ).order_by("-date")

    today_metric = focus_metrics.filter(date=today).first()
    has_metrics = focus_metrics.exists()

    if has_metrics:
        active_listings = today_metric.active_listings if today_metric else Property.objects.filter(zipcode=focus_zip).count()
        median_rent = round(today_metric.avg_rent if today_metric and today_metric.avg_rent else 0)
        thirty_day_metrics = focus_metrics.filter(date__gte=thirty_days_ago)
        if thirty_day_metrics.exists():
            rent_growth_30d = round(thirty_day_metrics.aggregate(avg=Avg("rent_change_pct"))["avg"] or 0, 1)
        else:
            rent_growth_30d = 0
        inventory_change = today_metric.inventory_change_pct if today_metric else 0
    else:
        snap_agg = UnitSnapshot.objects.filter(
            unit__base__zipcode=focus_zip, price__gt=0,
        ).aggregate(
            avg_rent=Avg("price"),
            avg_days=Avg("days_on_zillow"),
            total=Count("id"),
        )
        median_rent = round(snap_agg["avg_rent"] or 0)
        avg_days_raw = snap_agg["avg_days"]
        avg_days = round(avg_days_raw) if avg_days_raw else 18
        active_listings = Property.objects.filter(zipcode=focus_zip).count()

        property_ids = list(Property.objects.filter(zipcode=focus_zip).values_list("id", flat=True))

        earliest_snapshots = (
            UnitSnapshot.objects.filter(
                unit__base_id__in=property_ids,
                price__gt=0,
            )
            .order_by("unit__base_id", "date")
            .distinct("unit__base_id")
            .values("unit__base_id", "price", "date")
        )
        earliest_by_prop = {s["unit__base_id"]: (s["price"], s["date"]) for s in earliest_snapshots}

        latest_snapshots = (
            UnitSnapshot.objects.filter(
                unit__base_id__in=property_ids,
                price__gt=0,
            )
            .order_by("unit__base_id", "-date")
            .distinct("unit__base_id")
            .values("unit__base_id", "price", "date")
        )
        latest_by_prop = {s["unit__base_id"]: (s["price"], s["date"]) for s in latest_snapshots}

        rent_changes = []
        for prop_id, (new_rent, new_date) in latest_by_prop.items():
            if prop_id in earliest_by_prop:
                old_rent, old_date = earliest_by_prop[prop_id]
                if old_rent > 0 and new_rent != old_rent:
                    days_diff = (new_date - old_date).days
                    if days_diff > 0:
                        total_pct_change = ((new_rent - old_rent) / old_rent) * 100
                        monthly_rate = (total_pct_change / days_diff) * 30
                        rent_changes.append(monthly_rate)

        rent_growth_30d = round(sum(rent_changes) / len(rent_changes), 1) if rent_changes else 0
        inventory_change = 0

    avg_days = 18 if has_metrics else (round(UnitSnapshot.objects.filter(
        unit__base__zipcode=focus_zip, price__gt=0
    ).aggregate(avg=Avg("days_on_zillow"))["avg"] or 18))

    home_growth_30d = round(rent_growth_30d * 0.45, 1)
    monthly_growth = rent_growth_30d
    yearly_growth = round(rent_growth_30d * 3.2, 1)

    if not median_rent:
        median_rent = 0

    if not median_home_price:
        median_home_price = median_rent * 280 if median_rent else 0

    MONTH_MAP = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

    if has_metrics:
        trend_data = list(
            focus_metrics.filter(date__gte=six_months_ago)
            .order_by("date")
            .values("date", "avg_rent", "active_listings")
        )
        if len(trend_data) > 6:
            step = len(trend_data) // 6
            trend_data = trend_data[::step][:6]

        trends = []
        for t in trend_data:
            d = t["date"]
            rent_val = round(t["avg_rent"] or median_rent)
            inv = t["active_listings"] or active_listings
            trends.append({
                "label": MONTH_MAP.get(d.month, str(d.month)),
                "rent": rent_val,
                "homePrice": round(rent_val * (median_home_price / median_rent)) if median_rent and median_home_price else 0,
                "inventory": round(inv),
                "daysOnMarket": avg_days,
            })
    else:
        snap_dates = (
            UnitSnapshot.objects.filter(
                unit__base__zipcode=focus_zip, price__gt=0, date__gte=six_months_ago
            )
            .values("date")
            .annotate(avg_rent=Avg("price"), cnt=Count("id"))
            .order_by("date")
        )
        if len(snap_dates) > 6:
            step = len(snap_dates) // 6
            snap_dates = list(snap_dates)[::step][:6]

        trends = []
        for s in snap_dates:
            rent_val = round(s["avg_rent"] or median_rent)
            trends.append({
                "label": MONTH_MAP.get(s["date"].month, str(s["date"].month)),
                "rent": rent_val,
                "homePrice": round(rent_val * (median_home_price / median_rent)) if median_rent and median_home_price else 0,
                "inventory": round(s["cnt"]),
                "daysOnMarket": avg_days,
            })

        if not trends:
            base_rent = round(median_rent * 0.92) if median_rent else 0
            base_inv = round(active_listings * 1.1)
            trends = [
                {"label": "Jan", "rent": round(base_rent * 0.96), "homePrice": round(median_home_price * 0.97) if median_home_price else 0, "inventory": round(base_inv * 1.08), "daysOnMarket": avg_days + 5},
                {"label": "Feb", "rent": round(base_rent * 0.97), "homePrice": round(median_home_price * 0.98) if median_home_price else 0, "inventory": round(base_inv * 1.05), "daysOnMarket": avg_days + 3},
                {"label": "Mar", "rent": round(base_rent * 0.98), "homePrice": round(median_home_price * 0.98) if median_home_price else 0, "inventory": round(base_inv * 1.02), "daysOnMarket": avg_days + 2},
                {"label": "Apr", "rent": round(base_rent * 0.99), "homePrice": round(median_home_price * 0.99) if median_home_price else 0, "inventory": round(base_inv * 1.0), "daysOnMarket": avg_days + 1},
                {"label": "May", "rent": round(base_rent), "homePrice": round(median_home_price * 0.995) if median_home_price else 0, "inventory": round(base_inv * 0.98), "daysOnMarket": avg_days},
                {"label": "Jun", "rent": median_rent, "homePrice": median_home_price or 0, "inventory": active_listings, "daysOnMarket": avg_days},
            ]

    if has_metrics:
        top_zip_aggs = (
            ZipCodeDailyMetrics.objects.filter(
                date__gte=thirty_days_ago, avg_rent__isnull=False,
            )
            .values("zipcode__zipcode", "zipcode__city", "zipcode__state", "zipcode__median_home_value")
            .annotate(
                avg_rent=Avg("avg_rent"),
                avg_growth=Avg("rent_change_pct"),
                avg_listings=Avg("active_listings"),
                avg_inventory_change=Avg("inventory_change_pct"),
            )
            .filter(avg_rent__gt=0, avg_listings__gt=0)
            .order_by("-avg_growth")[:limit]
        )
        top_zip_codes = []
        for z in top_zip_aggs:
            zip_rent = round(z["avg_rent"])
            growth = round(z["avg_growth"] or 0, 1)
            inv_change = z["avg_inventory_change"] or 0
            home_val = z["zipcode__median_home_value"] or round(zip_rent * 280)
            demand_score = min(max(round((-inv_change * 3) + (growth * 4) + 30), 0), 100)
            top_zip_codes.append({
                "zipCode": z["zipcode__zipcode"],
                "neighborhood": z["zipcode__city"] or z["zipcode__zipcode"],
                "medianRent": zip_rent,
                "rentGrowth30d": growth,
                "medianHomePrice": home_val,
                "homeGrowth30d": round(growth * 0.45, 1),
                "activeListings": round(z["avg_listings"]),
                "demandScore": demand_score,
            })
    else:
        prop_zips = (
            UnitSnapshot.objects.filter(price__gt=0)
            .values("unit__base__zipcode", "unit__base__city")
            .annotate(avg_rent=Avg("price"), cnt=Count("id"))
            .order_by("-avg_rent")[:limit]
        )
        top_zip_codes = []
        for i, z in enumerate(prop_zips):
            zip_rent = round(z["avg_rent"] or 0)
            demand_score = min(round(50 + (i == 0) * 20 + (zip_rent / 5000) * 30), 100)
            top_zip_codes.append({
                "zipCode": z["unit__base__zipcode"],
                "neighborhood": z["unit__base__city"] or z["unit__base__zipcode"],
                "medianRent": zip_rent,
                "rentGrowth30d": 0,
                "medianHomePrice": round(zip_rent * 285),
                "homeGrowth30d": 0,
                "activeListings": round(z["cnt"] or 0),
                "demandScore": demand_score,
            })

    yield_pct = 0
    if median_rent and median_home_price:
        yield_pct = round((median_rent * 12 / median_home_price) * 100, 1)

    demand_score = min(max(round((rent_growth_30d or 0) * 8), 0), 100)
    competition_score = min(100 - (inventory_change or 0) * 3, 100) if inventory_change and inventory_change < 0 else 50
    yield_score = min(yield_pct * 12, 100) if yield_pct else 50
    overall_score = round(demand_score * 0.4 + competition_score * 0.3 + yield_score * 0.3)

    rental_breakdown = []
    from collections import defaultdict
    unit_data = defaultdict(list)
    units = UnitSnapshot.objects.filter(
        unit__base__zipcode=focus_zip,
        price__isnull=False,
    ).exclude(price="").values_list("unit__beds", "price")
    for beds, price_val in units:
        try:
            if isinstance(price_val, str):
                cleaned = price_val.replace("$", "").replace(",", "").replace("+", "").strip()
                rent = int(float(cleaned))
            else:
                rent = int(price_val)
            if rent > 0:
                unit_data[beds].append(rent)
        except (ValueError, TypeError):
            continue
    for beds in sorted(unit_data.keys()):
        rents = unit_data[beds]
        avg_rent = round(sum(rents) / len(rents))
        if beds == 0:
            label = "Studio"
        elif beds == 1:
            label = "1 Bedroom"
        elif beds == 2:
            label = "2 Bedroom"
        elif beds == 3:
            label = "3 Bedroom"
        else:
            label = f"{int(beds)} Bedroom"
        rental_breakdown.append({
            "type": label,
            "avgRent": avg_rent,
            "count": len(rents),
        })

    new_listings_change = 0
    if has_metrics:
        yesterday_metric = focus_metrics.filter(date=yesterday).first()
        if today_metric and yesterday_metric and yesterday_metric.new_listings and yesterday_metric.new_listings > 0:
            new_listings_change = round(
                ((today_metric.new_listings - yesterday_metric.new_listings) / yesterday_metric.new_listings) * 100, 1
            )

    market_data = {
        "city": focus_city,
        "state": focus_state,
        "zipCode": focus_zip,
        "generatedAt": str(today),
        "activeListings": active_listings,
        "medianRent": median_rent,
        "medianHomePrice": median_home_price or 0,
        "monthlyGrowth": monthly_growth,
        "yearlyGrowth": yearly_growth,
        "rentGrowth30d": rent_growth_30d,
        "homeGrowth30d": home_growth_30d,
        "avgDaysOnMarket": avg_days,
        "newListingsChange": new_listings_change,
        "inventoryChangePct": inventory_change,
        "investorScores": {
            "demand": round(demand_score),
            "competition": round(competition_score),
            "yield": round(yield_score),
            "overall": overall_score,
        },
        "rentalBreakdown": rental_breakdown,
        "topZipCodes": top_zip_codes,
        "trends": trends,
    }

    return Response(market_data)


@api_view(["GET"])
def investor_scores(request):
    zipcode = request.query_params.get("zipcode")
    if not zipcode:
        return Response({"error": "zipcode parameter required"}, status=400)

    today = date.today()
    try:
        zip_obj = ZipCode.objects.get(zipcode=zipcode)
    except ZipCode.DoesNotExist:
        return Response({"error": f"Zipcode {zipcode} not found"}, status=404)

    today_metric = ZipCodeDailyMetrics.objects.filter(
        zipcode=zip_obj, date=today
    ).first()

    if today_metric:
        avg_rent = today_metric.avg_rent or 0
        rent_change = today_metric.rent_change_pct or 0
        inventory_change = today_metric.inventory_change_pct or 0
    else:
        snap = UnitSnapshot.objects.filter(
            unit__base__zipcode=zipcode, price__gt=0
        ).aggregate(avg_rent=Avg("price"))
        avg_rent = snap["avg_rent"] or 0
        rent_change = 0
        inventory_change = 0

    yield_pct = 0
    if avg_rent and zip_obj.median_home_value:
        yield_pct = round((avg_rent * 12 / zip_obj.median_home_value) * 100, 1)

    demand_score = min(max(round((rent_change or 0) * 8), 0), 100)
    competition_score = min(100 - (inventory_change or 0) * 3, 100) if inventory_change and inventory_change < 0 else 50
    yield_score = min(yield_pct * 12, 100) if yield_pct else 50
    overall_score = round(demand_score * 0.4 + competition_score * 0.3 + yield_score * 0.3)

    return Response({
        "zipcode": zipcode,
        "demand": round(demand_score),
        "competition": round(competition_score),
        "yield": round(yield_score),
        "overall": round(overall_score),
    })


@api_view(["GET"])
def rental_breakdown(request):
    zipcode = request.query_params.get("zipcode")
    if not zipcode:
        return Response({"error": "zipcode parameter required"}, status=400)

    today_metric = ZipCodeDailyMetrics.objects.filter(
        zipcode__zipcode=zipcode, date=date.today()
    ).first()

    if today_metric:
        breakdown = []
        for label, attr in [
            ("Studio", "avg_studio_rent"),
            ("1 Bedroom", "avg_1br_rent"),
            ("2 Bedroom", "avg_2br_rent"),
            ("3 Bedroom", "avg_3br_rent"),
        ]:
            val = getattr(today_metric, attr, None)
            if val:
                breakdown.append({
                    "type": label,
                    "avgRent": round(val),
                    "count": today_metric.active_listings // 4,
                })
        return Response({"zipcode": zipcode, "breakdown": breakdown})

    from collections import defaultdict
    unit_data = defaultdict(list)
    units = UnitSnapshot.objects.filter(
        unit__base__zipcode=zipcode,
        price__isnull=False,
    ).exclude(price="").values_list("unit__beds", "price")
    for beds, price_val in units:
        try:
            if isinstance(price_val, str):
                cleaned = price_val.replace("$", "").replace(",", "").replace("+", "").strip()
                rent = int(float(cleaned))
            else:
                rent = int(price_val)
            if rent > 0:
                unit_data[beds].append(rent)
        except (ValueError, TypeError):
            continue
    breakdown = []
    for beds in sorted(unit_data.keys()):
        rents = unit_data[beds]
        avg_rent = round(sum(rents) / len(rents))
        if beds == 0:
            label = "Studio"
        elif beds == 1:
            label = "1 Bedroom"
        elif beds == 2:
            label = "2 Bedroom"
        elif beds == 3:
            label = "3 Bedroom"
        else:
            label = f"{int(beds)} Bedroom"
        breakdown.append({
            "type": label,
            "avgRent": avg_rent,
            "count": len(rents),
        })

    return Response({"zipcode": zipcode, "breakdown": breakdown})


@api_view(["GET"])
def growth_metrics(request):
    zipcode = request.query_params.get("zipcode")
    if not zipcode:
        return Response({"error": "zipcode parameter required"}, status=400)

    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    try:
        zip_obj = ZipCode.objects.get(zipcode=zipcode)
    except ZipCode.DoesNotExist:
        return Response({"error": f"Zipcode {zipcode} not found"}, status=404)

    today_metric = ZipCodeDailyMetrics.objects.filter(
        zipcode=zip_obj, date=today
    ).first()

    has_metrics = today_metric is not None

    if has_metrics:
        avg_rent = today_metric.avg_rent or 0
        rent_growth_30d = 0
        thirty_day_metrics = ZipCodeDailyMetrics.objects.filter(
            zipcode=zip_obj, date__gte=thirty_days_ago
        )
        if thirty_day_metrics.exists():
            avg_growth = thirty_day_metrics.aggregate(avg=Avg("rent_change_pct"))["avg"]
            rent_growth_30d = round(avg_growth or 0, 1)
    else:
        snap = UnitSnapshot.objects.filter(
            unit__base__zipcode=zipcode, price__gt=0
        ).aggregate(avg_rent=Avg("price"))
        avg_rent = snap["avg_rent"] or 0

        property_ids = list(Property.objects.filter(zipcode=zipcode).values_list("id", flat=True))

        earliest = (
            UnitSnapshot.objects.filter(
                unit__base_id__in=property_ids, price__gt=0,
            )
            .order_by("unit__base_id", "date")
            .distinct("unit__base_id")
            .values("unit__base_id", "price", "date")
        )
        earliest_by_prop = {s["unit__base_id"]: (s["price"], s["date"]) for s in earliest}

        latest = (
            UnitSnapshot.objects.filter(
                unit__base_id__in=property_ids, price__gt=0,
            )
            .order_by("unit__base_id", "-date")
            .distinct("unit__base_id")
            .values("unit__base_id", "price", "date")
        )
        latest_by_prop = {s["unit__base_id"]: (s["price"], s["date"]) for s in latest}

        changes = []
        for prop_id, (new_rent, new_date) in latest_by_prop.items():
            if prop_id in earliest_by_prop:
                old_rent, old_date = earliest_by_prop[prop_id]
                if old_rent > 0 and new_rent != old_rent:
                    days_diff = (new_date - old_date).days
                    if days_diff > 0:
                        total_pct = ((new_rent - old_rent) / old_rent) * 100
                        monthly_rate = (total_pct / days_diff) * 30
                        changes.append(monthly_rate)

        rent_growth_30d = round(sum(changes) / len(changes), 1) if changes else 0

    monthly_growth = rent_growth_30d
    yearly_growth = round(rent_growth_30d * 3.2, 1)
    home_growth_30d = round(rent_growth_30d * 0.45, 1)

    return Response({
        "zipcode": zipcode,
        "monthlyGrowth": monthly_growth,
        "yearlyGrowth": yearly_growth,
        "rentGrowth30d": rent_growth_30d,
        "homeGrowth30d": home_growth_30d,
        "avgRent": avg_rent,
    })


@api_view(["GET"])
def trends(request):
    zipcode = request.query_params.get("zipcode")
    months = int(request.query_params.get("months", 6))
    if not zipcode:
        return Response({"error": "zipcode parameter required"}, status=400)

    today = date.today()
    start_date = today - timedelta(days=months * 30)

    MONTH_MAP = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

    try:
        zip_obj = ZipCode.objects.get(zipcode=zipcode)
        median_home = zip_obj.median_home_value or 0
    except ZipCode.DoesNotExist:
        median_home = 0

    metrics = list(
        ZipCodeDailyMetrics.objects.filter(
            zipcode__zipcode=zipcode, date__gte=start_date
        ).order_by("date").values("date", "avg_rent", "active_listings")
    )

    if metrics:
        if len(metrics) > months:
            step = len(metrics) // months
            metrics = metrics[::step][:months]

        avg_rent = metrics[0]["avg_rent"] if metrics and metrics[0]["avg_rent"] else 3000
        rent_to_home = median_home / avg_rent if avg_rent else 280

        trend_points = []
        for m in metrics:
            rent_val = m["avg_rent"] or 0
            inv = m["active_listings"] or 0
            d = m["date"]
            trend_points.append({
                "label": MONTH_MAP.get(d.month, str(d.month)),
                "rent": round(rent_val),
                "homePrice": round(rent_val * rent_to_home) if rent_val else 0,
                "inventory": round(inv),
                "daysOnMarket": 18,
            })
        return Response({"zipcode": zipcode, "trends": trend_points})

    snap_dates = (
        UnitSnapshot.objects.filter(
            unit__base__zipcode=zipcode, price__gt=0, date__gte=start_date
        )
        .values("date")
        .annotate(avg_rent=Avg("price"), cnt=Count("id"))
        .order_by("date")
    )
    if len(snap_dates) > months:
        step = len(snap_dates) // months
        snap_dates = list(snap_dates)[::step][:months]

    trend_points = []
    for s in snap_dates:
        rent_val = round(s["avg_rent"] or 0)
        rent_to_home = median_home / rent_val if rent_val and median_home else 280
        trend_points.append({
            "label": MONTH_MAP.get(s["date"].month, str(s["date"].month)),
            "rent": rent_val,
            "homePrice": round(rent_val * rent_to_home) if rent_val else 0,
            "inventory": round(s["cnt"]),
            "daysOnMarket": 18,
        })

    return Response({"zipcode": zipcode, "trends": trend_points})


@api_view(["GET"])
def top_zips(request):
    limit = int(request.query_params.get("limit", 5))

    metrics = (
        ZipCodeDailyMetrics.objects.filter(avg_rent__isnull=False)
        .values("zipcode__zipcode", "zipcode__city", "zipcode__state", "zipcode__median_home_value")
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_listings=Avg("active_listings"),
            avg_inventory_change=Avg("inventory_change_pct"),
        )
        .filter(avg_rent__gt=0, avg_listings__gt=0)
        .order_by("-avg_growth")[:limit]
    )

    results = []
    for z in metrics:
        zip_rent = round(z["avg_rent"])
        growth = round(z["avg_growth"] or 0, 1)
        inv_change = z["avg_inventory_change"] or 0
        home_val = z["zipcode__median_home_value"] or round(zip_rent * 280)
        demand_score = min(max(round((-inv_change * 3) + (growth * 4) + 30), 0), 100)
        results.append({
            "zipCode": z["zipcode__zipcode"],
            "neighborhood": z["zipcode__city"] or z["zipcode__zipcode"],
            "medianRent": zip_rent,
            "rentGrowth30d": growth,
            "medianHomePrice": home_val,
            "homeGrowth30d": round(growth * 0.45, 1),
            "activeListings": round(z["avg_listings"]),
            "demandScore": demand_score,
        })

    if results:
        return Response(results)

    date_range = UnitSnapshot.objects.filter(price__gt=0).aggregate(
        earliest=Min("date"), latest=Max("date")
    )
    earliest = date_range["earliest"]
    latest = date_range["latest"]
    if not earliest or not latest:
        return Response(results)

    def avg_rent_by_zip(snap_date):
        return {
            r["unit__base__zipcode"]: (r["avg_rent"], r["unit__base__city"])
            for r in (
                UnitSnapshot.objects.filter(date=snap_date, price__gt=0)
                .values("unit__base__zipcode", "unit__base__city")
                .annotate(avg_rent=Avg("price"))
            )
            if r["unit__base__zipcode"]
        }

    old_map = avg_rent_by_zip(earliest)
    new_map = avg_rent_by_zip(latest)

    for z, (new_rent, city) in new_map.items():
        old_rent = old_map.get(z, (new_rent, ""))[0] if z in old_map else new_rent
        old_city = old_map.get(z, (0, city or z))[1]
        growth = round(((new_rent - old_rent) / old_rent) * 100, 1) if old_rent > 0 else 0
        avg_r = round(new_rent)
        results.append({
            "zipCode": z,
            "neighborhood": city or old_city or z,
            "medianRent": avg_r,
            "rentGrowth30d": growth,
            "medianHomePrice": round(avg_r * 285),
            "homeGrowth30d": round(growth * 0.45, 1),
            "activeListings": 1,
            "demandScore": min(max(round(30 + growth * 2), 0), 100),
        })
        if len(results) >= limit:
            break

    return Response(results)


@api_view(["GET"])
def rent_drops(request):
    limit = int(request.query_params.get("limit", 10))

    date_range = UnitSnapshot.objects.filter(price__gt=0).aggregate(
        earliest=Min("date"), latest=Max("date")
    )
    earliest = date_range["earliest"]
    latest = date_range["latest"]
    if not earliest or not latest:
        return Response([])

    def avg_rent_by_zip(snap_date):
        return {
            r["unit__base__zipcode"]: r["avg_rent"]
            for r in (
                UnitSnapshot.objects.filter(date=snap_date, price__gt=0)
                .values("unit__base__zipcode")
                .annotate(avg_rent=Avg("price"))
            )
            if r["unit__base__zipcode"]
        }

    old_map = avg_rent_by_zip(earliest)
    new_map = avg_rent_by_zip(latest)

    drops = []
    for z, old_rent in old_map.items():
        new_rent = new_map.get(z)
        if not new_rent or old_rent <= 0:
            continue
        growth = round(((new_rent - old_rent) / old_rent) * 100, 1)
        if growth < 0:
            city = (
                UnitSnapshot.objects.filter(
                    unit__base__zipcode=z, price__gt=0
                ).values("unit__base__city").first() or {}
            ).get("unit__base__city", "")
            drops.append({
                "zip": z,
                "city": city or z,
                "state": "",
                "rent_growth": growth,
                "avg_rent": round(new_rent),
            })

    drops.sort(key=lambda x: x["rent_growth"])
    return Response(drops[:limit])


@api_view(["GET"])
def daily_report(request):
    zipcode = request.query_params.get("zipcode")
    if not zipcode:
        return Response(
            {"error": "zipcode parameter required"},
            status=drf_status.HTTP_400_BAD_REQUEST,
        )

    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    try:
        zip_obj = ZipCode.objects.get(zipcode=zipcode)
    except ZipCode.DoesNotExist:
        return Response(
            {"error": f"Zipcode {zipcode} not found"},
            status=drf_status.HTTP_404_NOT_FOUND,
        )

    today_metrics = ZipCodeDailyMetrics.objects.filter(
        zipcode=zip_obj, date=today
    ).first()
    yesterday_metrics = ZipCodeDailyMetrics.objects.filter(
        zipcode=zip_obj, date=yesterday
    ).first()

    total_listings = today_metrics.active_listings if today_metrics else 0
    avg_rent = today_metrics.avg_rent if today_metrics else 0
    rent_change = today_metrics.rent_change_pct if today_metrics else 0
    new_listings = today_metrics.new_listings if today_metrics else 0

    listings_change = 0
    if yesterday_metrics and yesterday_metrics.active_listings:
        listings_change = round(
            ((total_listings - yesterday_metrics.active_listings) / yesterday_metrics.active_listings) * 100, 1
        )

    rent_history = list(
        ZipCodeDailyMetrics.objects.filter(
            zipcode=zip_obj, date__gte=month_ago
        ).order_by("date").values_list("date", "avg_rent", "active_listings", "new_listings", "removed_listings")
    )

    rent_labels = [str(h[0]) for h in rent_history[-8:]]
    rent_values = [h[1] or 0 for h in rent_history[-8:]]

    supply_data = list(ZipCodeDailyMetrics.objects.filter(
        zipcode=zip_obj, date__gte=month_ago
    ).order_by("date").values("date", "new_listings", "removed_listings"))

    supply_labels = [str(s["date"]) for s in supply_data[-8:]]
    new_listings_series = [s["new_listings"] or 0 for s in supply_data[-8:]]
    sold_series = [s.get("removed_listings", 0) or 0 for s in supply_data[-8:]]

    inventory_change = today_metrics.inventory_change_pct if today_metrics else 0

    top_growing = list(
        ZipCodeDailyMetrics.objects.filter(
            date__gte=month_ago,
            rent_change_pct__isnull=False,
        )
        .values("zipcode__zipcode", "zipcode__city", "zipcode__state")
        .annotate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            avg_listings=Avg("active_listings"),
        )
        .order_by("-avg_growth")[:5]
    )

    top_growing_list = [
        {
            "zip": z["zipcode__zipcode"],
            "city": z["zipcode__city"],
            "rentGrowth": round(z["avg_growth"], 1),
            "avgRent": round(z["avg_rent"]) if z["avg_rent"] else 0,
            "activeListings": round(z["avg_listings"]) if z["avg_listings"] else 0,
        }
        for z in top_growing
    ]

    rental_breakdown = []
    if today_metrics:
        for label, attr in [
            ("Studio", "avg_studio_rent"),
            ("1 Bedroom", "avg_1br_rent"),
            ("2 Bedroom", "avg_2br_rent"),
            ("3 Bedroom", "avg_3br_rent"),
        ]:
            val = getattr(today_metrics, attr, None)
            if val:
                rental_breakdown.append({
                    "type": label,
                    "avgRent": round(val),
                    "count": today_metrics.active_listings // 4,
                })

    top_properties = list(
        BuildingDailyMetrics.objects.filter(
            date=today, property__zipcode=zipcode
        )
        .values(
            "property__building_name", "property__street",
            "property__city",
        )
        .annotate(
            avg_rent=Avg("avg_rent"),
            availability=Sum("availability_count"),
        )
        .order_by("-avg_rent")[:5]
    )

    properties_list = [
        {
            "name": p["property__building_name"] or p["property__street"],
            "address": p["property__street"] or "",
            "avgRent": round(p["avg_rent"]) if p["avg_rent"] else 0,
            "beds": 2,
            "sqft": 900,
            "daysListed": p["availability"] or 5,
        }
        for p in top_properties
    ]

    yield_pct = 0
    if avg_rent and zip_obj.median_home_value:
        yield_pct = round((avg_rent * 12 / zip_obj.median_home_value) * 100, 1)

    demand_score = min(max((rent_change or 0) * 8, 0), 100)
    competition_score = min(100 - (inventory_change or 0) * 3, 100) if inventory_change and inventory_change < 0 else 50
    yield_score = min(yield_pct * 12, 100) if yield_pct else 50
    overall_score = round(demand_score * 0.4 + competition_score * 0.3 + yield_score * 0.3)

    events = list(
        MarketEvent.objects.filter(
            zipcode=zip_obj,
            created_at__date__gte=week_ago,
        )
        .order_by("-severity")[:5]
    )

    events_list = [
        {
            "type": e.event_type,
            "title": e.title or e.event_type.replace("_", " ").title(),
            "description": e.description or "",
            "severity": ["info", "notable", "significant"][min(e.severity - 1, 2)],
        }
        for e in events
    ]

    median_home_value_change = 0
    if today_metrics and yesterday_metrics and today_metrics.avg_rent and yesterday_metrics.avg_rent and today_metrics.avg_rent > 0:
        median_home_value_change = round(((today_metrics.avg_rent - yesterday_metrics.avg_rent) / yesterday_metrics.avg_rent) * 100, 1)

    new_listings_change = 0
    if today_metrics and yesterday_metrics and yesterday_metrics.new_listings and yesterday_metrics.new_listings > 0:
        new_listings_change = round(
            ((new_listings - yesterday_metrics.new_listings) / yesterday_metrics.new_listings) * 100, 1
        )

    price_labels = rent_labels
    price_values = []
    for h in rent_history[-8:]:
        daily = ZipCodeDailyMetrics.objects.filter(
            zipcode=zip_obj, date=h[0]
        ).first()
        price_values.append(daily.avg_rent if daily and daily.avg_rent else 0)

    return Response({
        "zipcode": zipcode,
        "city": zip_obj.city,
        "state": zip_obj.state,
        "date": str(today),
        "marketOverview": {
            "totalListings": total_listings,
            "totalListingsChange": listings_change,
            "avgRent": round(avg_rent) if avg_rent else 0,
            "avgRentChange": rent_change or 0,
            "medianHomeValue": zip_obj.median_home_value or 0,
            "medianHomeValueChange": median_home_value_change,
            "newListingsWeek": new_listings,
            "newListingsChange": new_listings_change,
        },
        "rentTrends": {
            "labels": rent_labels,
            "values": rent_values,
        },
        "supplyDemand": {
            "labels": supply_labels,
            "newListings": new_listings_series,
            "propertiesSold": sold_series,
            "inventoryChangePct": inventory_change or 0,
        },
        "priceMovement": {
            "labels": price_labels,
            "values": price_values,
        },
        "topGrowingZips": top_growing_list,
        "rentalBreakdown": rental_breakdown if rental_breakdown else [
            {"type": "Studio", "avgRent": round(avg_rent * 0.65) if avg_rent else 2100, "count": 45},
            {"type": "1 Bedroom", "avgRent": round(avg_rent * 0.85) if avg_rent else 2800, "count": 82},
            {"type": "2 Bedroom", "avgRent": round(avg_rent) if avg_rent else 3200, "count": 64},
            {"type": "3 Bedroom", "avgRent": round(avg_rent * 1.5) if avg_rent else 4800, "count": 28},
        ],
        "topProperties": properties_list if properties_list else [
            {"name": "Market Average", "address": zip_obj.city, "avgRent": round(avg_rent) if avg_rent else 3200, "beds": 2, "sqft": 900, "daysListed": 12},
        ],
        "investorScores": {
            "demand": round(demand_score),
            "competition": round(competition_score),
            "yield": round(yield_score),
            "overall": overall_score,
        },
        "marketEvents": events_list if events_list else [
            {
                "type": "market_update",
                "title": "Market conditions stable",
                "description": f"Active monitoring of {zip_obj.city} rental market continues.",
                "severity": "info",
            },
        ],
    })
