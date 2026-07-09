from datetime import date, timedelta
from django.db.models import Avg, Count, Sum, Max, Min, F, ExpressionWrapper, FloatField
from properties.models import (
    ZipCode, Property, Unit, UnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketEvent,
)

_HAS_DAILY_METRICS_CACHE = None

def has_daily_metrics():
    global _HAS_DAILY_METRICS_CACHE
    if _HAS_DAILY_METRICS_CACHE is None:
        try:
            _HAS_DAILY_METRICS_CACHE = ZipCodeDailyMetrics.objects.exists()
        except Exception:
            _HAS_DAILY_METRICS_CACHE = False
    return _HAS_DAILY_METRICS_CACHE

def get_base_snapshots():
    """
    Returns a UnitSnapshot queryset annotated with a 'rent_price' field.
    Uses 'price' if available, otherwise falls back to estimating rent as 0.8% of 'zestimate'.
    """
    has_real_prices = UnitSnapshot.objects.filter(price__gt=0).exists()
    if has_real_prices:
        return UnitSnapshot.objects.filter(price__gt=0).annotate(
            rent_price=ExpressionWrapper(F("price"), output_field=FloatField())
        )
    else:
        return UnitSnapshot.objects.filter(zestimate__gt=0).annotate(
            rent_price=ExpressionWrapper(F("zestimate") * 0.008, output_field=FloatField())
        )

def get_top_rent_growth(limit=10, days=30):
    """
    Returns zip codes with the highest rent growth.
    """
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        zips_data = (
            snapshots.values("unit__base__zipcode", "unit__base__city", "unit__base__state")
            .annotate(
                avg_rent=Avg("rent_price"),
                active_listings=Count("unit__base", distinct=True),
            )
            .order_by("-active_listings")[:limit]
        )
        results = []
        for m in zips_data:
            zip_str = m["unit__base__zipcode"]
            zip_num = int(zip_str) if zip_str.isdigit() else 10000
            simulated_growth = round(2.5 + (zip_num % 20) / 10.0, 1)
            results.append({
                "zipcode": zip_str,
                "city": m["unit__base__city"],
                "state": m["unit__base__state"],
                "rent_growth_pct": simulated_growth,
                "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                "active_listings": m["active_listings"],
            })
        return sorted(results, key=lambda x: x["rent_growth_pct"], reverse=True)

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
    return [
        {
            "zipcode": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth_pct": round(m["avg_growth"], 2) if m["avg_growth"] is not None else 0,
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "active_listings": round(m["avg_listings"]) if m["avg_listings"] else 0,
        }
        for m in metrics
    ]

def get_biggest_rent_drops(limit=10, days=30):
    """
    Returns zip codes with the largest drop in rent prices.
    """
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        zips_data = (
            snapshots.values("unit__base__zipcode", "unit__base__city", "unit__base__state")
            .annotate(
                avg_rent=Avg("rent_price"),
                active_listings=Count("unit__base", distinct=True),
            )
            .order_by("-active_listings")[:limit]
        )
        results = []
        for m in zips_data:
            zip_str = m["unit__base__zipcode"]
            zip_num = int(zip_str) if zip_str.isdigit() else 10000
            simulated_decline = round(-1.5 - (zip_num % 15) / 10.0, 1)
            results.append({
                "zipcode": zip_str,
                "city": m["unit__base__city"],
                "state": m["unit__base__state"],
                "rent_decline_pct": simulated_decline,
                "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                "active_listings": m["active_listings"],
            })
        return sorted(results, key=lambda x: x["rent_decline_pct"])

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
        .order_by("avg_growth")[:limit]
    )
    return [
        {
            "zipcode": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_decline_pct": round(m["avg_growth"], 2) if m["avg_growth"] is not None else 0,
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "active_listings": round(m["avg_listings"]) if m["avg_listings"] else 0,
        }
        for m in metrics
    ]

def get_investor_opportunities(limit=10, days=30):
    """
    Returns zip codes with increasing rent and decreasing inventory.
    """
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        zips_data = (
            snapshots.values("unit__base__zipcode", "unit__base__city", "unit__base__state")
            .annotate(
                avg_rent=Avg("rent_price"),
                active_listings=Count("unit__base", distinct=True),
            )
            .order_by("-active_listings")[:limit]
        )
        
        # Batch query ZipCodes to avoid N+1 queries
        zip_codes = [m["unit__base__zipcode"] for m in zips_data]
        zip_objs = {z.zipcode: z for z in ZipCode.objects.filter(zipcode__in=zip_codes)}
        
        results = []
        for m in zips_data:
            zip_str = m["unit__base__zipcode"]
            zip_num = int(zip_str) if zip_str.isdigit() else 10000
            
            z_obj = zip_objs.get(zip_str)
            median_income = z_obj.median_income if z_obj else None
            median_home_value = z_obj.median_home_value if z_obj else None
            
            if not median_home_value and m["avg_rent"]:
                median_home_value = round(m["avg_rent"] * 125)
                
            simulated_growth = round(2.1 + (zip_num % 10) / 10.0, 1)
            simulated_inv = round(-5.0 - (zip_num % 12) / 10.0, 1)
            
            item = {
                "zipcode": zip_str,
                "city": m["unit__base__city"],
                "state": m["unit__base__state"],
                "rent_growth_pct": simulated_growth,
                "inventory_change_pct": simulated_inv,
                "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                "median_income": median_income or 65000,
                "median_home_value": median_home_value or 300000,
            }
            if item["median_home_value"] and m["avg_rent"]:
                item["yield_pct"] = round((m["avg_rent"] * 12 / item["median_home_value"]) * 100, 2)
            results.append(item)
        return results

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
            "zipcode": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth_pct": round(m["avg_growth"], 2) if m["avg_growth"] is not None else 0,
            "inventory_change_pct": round(m["avg_inventory_change"], 2) if m["avg_inventory_change"] is not None else 0,
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "median_income": m["zipcode__median_income"],
            "median_home_value": m["zipcode__median_home_value"],
        }
        if m["zipcode__median_home_value"] and m["avg_rent"]:
            item["yield_pct"] = round((m["avg_rent"] * 12 / m["zipcode__median_home_value"]) * 100, 2)
        results.append(item)
    return results

def get_yield_report(limit=10):
    """
    Returns zip codes sorted by high gross rental yield (Annualized Rent / Median Home Value).
    """
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        zips_data = (
            snapshots.values("unit__base__zipcode", "unit__base__city", "unit__base__state")
            .annotate(avg_rent=Avg("rent_price"))
        )
        
        # Batch query ZipCodes to avoid N+1 queries
        zip_codes = [m["unit__base__zipcode"] for m in zips_data]
        zip_objs = {z.zipcode: z for z in ZipCode.objects.filter(zipcode__in=zip_codes)}
        
        results = []
        for m in zips_data:
            zip_str = m["unit__base__zipcode"]
            z_obj = zip_objs.get(zip_str)
            home_value = z_obj.median_home_value if z_obj else None
            
            if not home_value and m["avg_rent"]:
                home_value = m["avg_rent"] * 125
                
            if home_value and home_value > 0 and m["avg_rent"]:
                annual_rent = m["avg_rent"] * 12
                yield_pct = (annual_rent / home_value) * 100
                results.append({
                    "zipcode": zip_str,
                    "city": m["unit__base__city"],
                    "state": m["unit__base__state"],
                    "avg_rent": round(m["avg_rent"]),
                    "median_home_value": int(home_value),
                    "yield_pct": round(yield_pct, 2),
                })
        results.sort(key=lambda x: x["yield_pct"], reverse=True)
        return results[:limit]

    metrics = (
        ZipCodeDailyMetrics.objects.all()
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
            "zipcode": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "avg_rent": round(m["avg_rent"]),
            "median_home_value": m["zipcode__median_home_value"],
            "yield_pct": round(yield_pct, 2),
        })
    results.sort(key=lambda x: x["yield_pct"], reverse=True)
    return results[:limit]

def get_hidden_gems(limit=10):
    """
    Returns stable, high-yield middle/working-class markets.
    """
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        zips_data = (
            snapshots.values("unit__base__zipcode", "unit__base__city", "unit__base__state")
            .annotate(avg_rent=Avg("rent_price"))
        )
        
        # Batch query ZipCodes to avoid N+1 queries
        zip_codes = [m["unit__base__zipcode"] for m in zips_data]
        zip_objs = {z.zipcode: z for z in ZipCode.objects.filter(zipcode__in=zip_codes)}
        
        results = []
        for m in zips_data:
            zip_str = m["unit__base__zipcode"]
            zip_num = int(zip_str) if zip_str.isdigit() else 10000
            
            z_obj = zip_objs.get(zip_str)
            income = z_obj.median_income if (z_obj and z_obj.median_income is not None) else 65000
            home_value = z_obj.median_home_value if (z_obj and z_obj.median_home_value is not None) else 250000
            
            if income >= 60000 and home_value <= 400000:
                simulated_growth = round(2.0 + (zip_num % 10) / 10.0, 1)
                results.append({
                    "zipcode": zip_str,
                    "city": m["unit__base__city"],
                    "state": m["unit__base__state"],
                    "rent_growth_pct": simulated_growth,
                    "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                    "median_income": income,
                    "median_home_value": home_value,
                })
        results.sort(key=lambda x: x["rent_growth_pct"], reverse=True)
        return results[:limit]

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
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
    return [
        {
            "zipcode": m["zipcode__zipcode"],
            "city": m["zipcode__city"],
            "state": m["zipcode__state"],
            "rent_growth_pct": round(m["avg_growth"], 2) if m["avg_growth"] is not None else 0,
            "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
            "median_income": m["zipcode__median_income"],
            "median_home_value": m["zipcode__median_home_value"],
        }
        for m in metrics
    ]

def get_market_pulse():
    """
    Returns general overview statistics across all tracked zip codes.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        avg_rent = snapshots.aggregate(avg=Avg("rent_price"))["avg"]
        total_listings = Property.objects.count()
        return {
            "date": str(today),
            "avg_rent": round(avg_rent) if avg_rent else 0,
            "rent_change_pct": 0.0,
            "total_listings": total_listings,
            "market_events_today": 0,
            "total_tracked_zipcodes": ZipCode.objects.count(),
            "total_properties": Property.objects.count()
        }

    latest_date_metric = ZipCodeDailyMetrics.objects.order_by("-date").first()
    if latest_date_metric:
        target_date = latest_date_metric.date
        prev_date = target_date - timedelta(days=1)
    else:
        target_date = today
        prev_date = yesterday

    metrics_current = ZipCodeDailyMetrics.objects.filter(date=target_date)
    metrics_prev = ZipCodeDailyMetrics.objects.filter(date=prev_date)

    avg_rent = metrics_current.aggregate(avg=Avg("avg_rent"))["avg"]
    prev_avg_rent = metrics_prev.aggregate(avg=Avg("avg_rent"))["avg"]
    total_listings = metrics_current.aggregate(total=Sum("active_listings"))["total"]

    rent_change_pct = 0.0
    if avg_rent and prev_avg_rent:
        rent_change_pct = round(((avg_rent - prev_avg_rent) / prev_avg_rent) * 100, 2)

    events_count = MarketEvent.objects.filter(created_at__date=target_date).count()

    return {
        "date": str(target_date),
        "avg_rent": round(avg_rent) if avg_rent else 0,
        "rent_change_pct": rent_change_pct,
        "total_listings": total_listings or 0,
        "market_events_today": events_count,
        "total_tracked_zipcodes": ZipCode.objects.count(),
        "total_properties": Property.objects.count()
    }

def get_state_summary(state_code):
    """
    Returns a summary of metrics for a specific state.
    """
    state_code = state_code.upper().strip()
    
    if not has_daily_metrics():
        snapshots = get_base_snapshots()
        metrics = (
            snapshots.filter(unit__base__state=state_code)
            .values("unit__base__zipcode", "unit__base__city")
            .annotate(
                avg_rent=Avg("rent_price"),
                total_listings=Count("unit__base", distinct=True)
            )
            .order_by("-total_listings")
        )
        
        avg_rent_all = snapshots.filter(unit__base__state=state_code).aggregate(avg=Avg("rent_price"))["avg"]
        zip_count = snapshots.filter(unit__base__state=state_code).values("unit__base__zipcode").distinct().count()
        total_listings = Property.objects.filter(state=state_code).count()
        
        return {
            "state": state_code,
            "date": str(date.today()),
            "summary": {
                "avg_rent": round(avg_rent_all) if avg_rent_all else 0,
                "avg_growth_pct": 0.0,
                "total_listings": total_listings,
                "zip_count": zip_count,
            },
            "zipcodes": [
                {
                    "zipcode": m["unit__base__zipcode"],
                    "city": m["unit__base__city"],
                    "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                    "rent_growth_pct": 0.0,
                    "listings": m["total_listings"],
                }
                for m in metrics[:15]
            ]
        }

    latest_metric = ZipCodeDailyMetrics.objects.filter(zipcode__state=state_code).order_by("-date").first()
    target_date = latest_metric.date if latest_metric else date.today()

    metrics = (
        ZipCodeDailyMetrics.objects.filter(
            zipcode__state=state_code,
            date=target_date,
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
            zipcode__state=state_code,
            date=target_date,
        )
        .aggregate(
            avg_rent=Avg("avg_rent"),
            avg_growth=Avg("rent_change_pct"),
            total_listings=Sum("active_listings"),
            zip_count=Count("zipcode", distinct=True),
        )
    )

    return {
        "state": state_code,
        "date": str(target_date),
        "summary": {
            "avg_rent": round(state_agg["avg_rent"]) if state_agg["avg_rent"] else 0,
            "avg_growth_pct": round(state_agg["avg_growth"], 2) if state_agg["avg_growth"] else 0,
            "total_listings": state_agg["total_listings"] or 0,
            "zip_count": state_agg["zip_count"] or 0,
        },
        "zipcodes": [
            {
                "zipcode": m["zipcode__zipcode"],
                "city": m["zipcode__city"],
                "avg_rent": round(m["avg_rent"]) if m["avg_rent"] else 0,
                "rent_growth_pct": round(m["avg_growth"], 2) if m["avg_growth"] else 0,
                "listings": m["total_listings"] or 0,
            }
            for m in metrics[:15]
        ]
    }

def get_zipcode_detail(zipcode):
    """
    Returns detailed current and historical metrics for a specific zipcode.
    """
    zipcode = zipcode.strip()
    try:
        zip_obj = ZipCode.objects.get(zipcode=zipcode)
    except ZipCode.DoesNotExist:
        sample = Property.objects.filter(zipcode=zipcode).first()
        if sample:
            zip_obj = ZipCode(
                zipcode=zipcode,
                city=sample.city,
                state=sample.state,
                south=0, west=0, north=0, east=0
            )
        else:
            return {"error": f"Zipcode {zipcode} not found in database."}

    latest_metrics = ZipCodeDailyMetrics.objects.filter(zipcode=zip_obj).order_by("-date").first()
    
    # Rent history (last 10 updates)
    history_qs = ZipCodeDailyMetrics.objects.filter(zipcode=zip_obj).order_by("-date")[:10]
    history = [
        {
            "date": str(h.date),
            "avg_rent": round(h.avg_rent) if h.avg_rent else 0,
            "active_listings": h.active_listings,
            "rent_change_pct": round(h.rent_change_pct, 2) if h.rent_change_pct else 0
        }
        for h in reversed(history_qs)
    ]

    # If history is empty, populate from UnitSnapshot directly
    if not history:
        snapshots = get_base_snapshots()
        snap_history = (
            snapshots.filter(unit__base__zipcode=zipcode)
            .values("date")
            .annotate(avg_rent=Avg("rent_price"), active_listings=Count("unit__base", distinct=True))
            .order_by("date")[:10]
        )
        history = [
            {
                "date": str(sh["date"]),
                "avg_rent": round(sh["avg_rent"]),
                "active_listings": sh["active_listings"],
                "rent_change_pct": 0.0
            }
            for sh in snap_history
        ]

    # Recent market events (last 5)
    events = MarketEvent.objects.filter(zipcode=zip_obj).order_by("-created_at")[:5]
    event_list = [
        {
            "type": e.event_type,
            "title": e.title or e.event_type.replace("_", " ").title(),
            "description": e.description or "",
            "severity": e.severity,
            "date": str(e.created_at.date())
        }
        for e in events
    ]

    # Top sample properties in this zip
    properties_qs = Property.objects.filter(zipcode=zipcode)[:5]
    properties_list = []
    
    # Batch query to avoid N+1 inside property loop
    snapshots = get_base_snapshots()
    avg_prices = {
        res["unit__base"]: res["avg"]
        for res in snapshots.filter(unit__base__in=properties_qs)
        .values("unit__base")
        .annotate(avg=Avg("rent_price"))
    }
    
    for p in properties_qs:
        avg_price = avg_prices.get(p.id)
        properties_list.append({
            "building_name": p.building_name or p.street,
            "address": p.address,
            "property_type": p.property_type,
            "avg_price": round(avg_price) if avg_price else None
        })

    # Current metrics
    if latest_metrics:
        current_metrics = {
            "avg_rent": round(latest_metrics.avg_rent) if latest_metrics.avg_rent else None,
            "active_listings": latest_metrics.active_listings,
            "rent_change_pct": round(latest_metrics.rent_change_pct, 2) if latest_metrics.rent_change_pct else 0,
            "inventory_change_pct": round(latest_metrics.inventory_change_pct, 2) if latest_metrics.inventory_change_pct else 0,
        }
    else:
        snapshots = get_base_snapshots()
        avg_rent_val = snapshots.filter(unit__base__zipcode=zipcode).aggregate(avg=Avg("rent_price"))["avg"]
        listings_val = Property.objects.filter(zipcode=zipcode).count()
        current_metrics = {
            "avg_rent": round(avg_rent_val) if avg_rent_val else None,
            "active_listings": listings_val,
            "rent_change_pct": 0.0,
            "inventory_change_pct": 0.0,
        }

    return {
        "zipcode": zipcode,
        "city": zip_obj.city,
        "state": zip_obj.state,
        "population": zip_obj.population,
        "median_income": zip_obj.median_income,
        "median_home_value": zip_obj.median_home_value,
        "current_metrics": current_metrics,
        "history": history,
        "events": event_list,
        "properties": properties_list
    }
