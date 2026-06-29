import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Avg, Sum, F
from datetime import date, timedelta

logger = logging.getLogger(__name__)

from .models import (
    ZipCode, Property, PropertySnapshot, PropertyUnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    RentHistory, PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
    PropertyPriceHistory, PropertyTaxHistory, PropertySchool,
)
from .serializers import (
    ZipCodeSerializer, PropertySerializer, PropertyCreateSerializer,
    PropertySnapshotSerializer, PropertyUnitSnapshotSerializer,
    ZipCodeDailyMetricsSerializer, BuildingDailyMetricsSerializer,
    MarketReportSerializer, RentHistorySerializer, PropertyPhotoSerializer,
    ZipCodeRankingSerializer, StateDailyMetricsSerializer, MarketEventSerializer,
    PropertyPriceHistorySerializer, PropertyTaxHistorySerializer, PropertySchoolSerializer,
)
from .analytics import (
    top_rent_growth, biggest_rent_drops, inventory_explosion,
    investor_opportunities, emerging_markets, hidden_gems,
    yield_report, luxury_markets, top_landlords, market_pulse,
    daily_digest, rent_history_by_zip, opportunity_score,
    state_summary, building_performance, smart_zip_pick,
)


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        source = self.request.query_params.get("source")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        zipcode = self.request.query_params.get("zipcode")
        property_type = self.request.query_params.get("property_type")
        management_company = self.request.query_params.get("management_company")
        search = self.request.query_params.get("search")

        if source:
            qs = qs.filter(source=source)
        if city:
            qs = qs.filter(city__icontains=city)
        if state:
            qs = qs.filter(state__icontains=state)
        if zipcode:
            qs = qs.filter(zipcode=zipcode)
        if property_type:
            qs = qs.filter(property_type=property_type)
        if management_company:
            qs = qs.filter(management_company__icontains=management_company)
        if search:
            qs = qs.filter(
                Q(address__icontains=search)
                | Q(street__icontains=search)
                | Q(building_name__icontains=search)
                | Q(management_company__icontains=search)
            )
        return qs


@api_view(["POST"])
def receive_listing(request):
    serializer = PropertyCreateSerializer(data=request.data)
    if serializer.is_valid():
        prop = serializer.save()
        return Response(
            PropertySerializer(prop).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def receive_listings_bulk(request):
    if not isinstance(request.data, list):
        return Response(
            {"error": "Expected a list of listings"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created = 0
    errors = []
    for i, listing in enumerate(request.data):
        serializer = PropertyCreateSerializer(data=listing)
        if serializer.is_valid():
            serializer.save()
            created += 1
        else:
            errors.append({"index": i, "errors": serializer.errors})

    return Response(
        {
            "created": created,
            "errors": len(errors),
            "error_details": errors[:10],
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
def receive_property_detail(request):
    zpid = request.data.get("zpid")
    if not zpid:
        return Response({"error": "zpid is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        prop = Property.objects.get(zpid=str(zpid))
    except Property.DoesNotExist:
        return Response({"error": f"Property with zpid {zpid} not found"}, status=status.HTTP_404_NOT_FOUND)

    detail_fields = [
        "bedrooms", "bathrooms", "living_area", "lot_size", "year_built",
        "property_type_detailed", "parking_features", "cooling", "heating",
        "flooring", "appliances", "interior_features", "exterior_features",
        "lot_features", "sewer", "water_source", "architectural_style",
        "garage_spaces", "hoa_fee", "total_fees", "zestimate",
        "property_tax_rate", "description",
    ]
    list_fields = {"parking_features", "appliances"}
    char_fields = {
        "cooling", "heating", "flooring", "interior_features",
        "exterior_features", "lot_features", "sewer", "water_source",
        "architectural_style", "property_type_detailed", "total_fees", "description",
    }
    float_fields = {"bedrooms", "bathrooms", "lot_size", "garage_spaces", "hoa_fee", "property_tax_rate"}
    int_fields = {"living_area", "year_built", "zestimate"}

    updated_fields = []
    for field in detail_fields:
        if field not in request.data:
            continue
        val = request.data[field]
        current = getattr(prop, field, None)
        if current not in (None, "", [], {}):
            continue
        if field in list_fields:
            if isinstance(val, list):
                setattr(prop, field, val)
            elif isinstance(val, str):
                setattr(prop, field, [val] if val else [])
            else:
                setattr(prop, field, [])
        elif field in char_fields:
            if isinstance(val, list):
                setattr(prop, field, ", ".join(str(v) for v in val))
            else:
                setattr(prop, field, str(val))
        elif field in float_fields:
            try:
                setattr(prop, field, float(val))
            except (TypeError, ValueError):
                continue
        elif field in int_fields:
            try:
                setattr(prop, field, int(val))
            except (TypeError, ValueError):
                continue
        else:
            setattr(prop, field, val)
        updated_fields.append(field)
    if updated_fields:
        try:
            prop.save(update_fields=updated_fields)
        except Exception as e:
            logger.warning("Failed to save property %s: %s", zpid, e)

    created = {"price_history": 0, "tax_history": 0, "schools": 0}

    price_history = request.data.get("price_history", [])
    if price_history and not prop.price_history.exists():
        for entry in price_history:
            try:
                PropertyPriceHistory.objects.create(
                    property=prop,
                    date=entry["date"],
                    price=int(entry.get("price") or 0),
                    price_per_sqft=int(entry["price_per_sqft"]) if entry.get("price_per_sqft") else None,
                    event=entry.get("event", ""),
                    source=entry.get("source", ""),
                )
                created["price_history"] += 1
            except Exception as e:
                logger.warning("Failed to save price history for %s: %s", zpid, e)

    tax_history = request.data.get("tax_history", [])
    if tax_history and not prop.tax_history.exists():
        for entry in tax_history:
            try:
                PropertyTaxHistory.objects.create(
                    property=prop,
                    date=entry["date"],
                    tax_amount=int(entry.get("tax_amount") or 0),
                    value=int(entry.get("value") or 0),
                    year=int(entry.get("year") or 0),
                )
                created["tax_history"] += 1
            except Exception as e:
                logger.warning("Failed to save tax history for %s: %s", zpid, e)

    schools = request.data.get("schools", [])
    if schools and not prop.schools.exists():
        for s in schools:
            try:
                PropertySchool.objects.create(
                    property=prop,
                    name=s.get("name", ""),
                    rating=s.get("rating"),
                    type=s.get("type", ""),
                    level=s.get("level", ""),
                    grades=s.get("grades", ""),
                    students_count=s.get("students_count"),
                    teacher_count=s.get("teacher_count"),
                    student_teacher_ratio=s.get("student_teacher_ratio"),
                    distance=s.get("distance"),
                    is_assigned=s.get("is_assigned", False),
                )
                created["schools"] += 1
            except Exception as e:
                logger.warning("Failed to save school for %s: %s", zpid, e)

    return Response({"status": "ok", "zpid": zpid, "updated_fields": updated_fields, "created": created}, status=status.HTTP_200_OK)


@api_view(["GET"])
def property_zpids(request):
    source = request.query_params.get("source", "zillow")
    qs = Property.objects.filter(source=source).exclude(zpid="").values_list("zpid", flat=True)
    numeric = [z for z in qs if z.isdigit()]
    return Response({"count": len(numeric), "zpids": numeric})


@api_view(["GET"])
def property_stats(request):
    total = Property.objects.count()
    by_source = {}
    for source, _ in Property.SOURCE_CHOICES:
        by_source[source] = Property.objects.filter(source=source).count()
    return Response({
        "total_properties": total,
        "by_source": by_source,
    })


class ZipCodeViewSet(viewsets.ModelViewSet):
    queryset = ZipCode.objects.all()
    serializer_class = ZipCodeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        zipcode = self.request.query_params.get("zipcode")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")

        if zipcode:
            qs = qs.filter(zipcode=zipcode)
        if city:
            qs = qs.filter(city__icontains=city)
        if state:
            qs = qs.filter(state__icontains=state)
        return qs

    @action(detail=False, methods=["get"])
    def all(self, request):
        zipcodes = ZipCode.objects.all()
        return Response({
            "count": zipcodes.count(),
            "results": ZipCodeSerializer(zipcodes, many=True).data,
        })

    @action(detail=False, methods=["get"])
    def geojson(self, request):
        zipcodes = ZipCode.objects.all()
        features = []
        for zc in zipcodes:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [zc.bbox],
                },
                "properties": {
                    "zipcode": zc.zipcode,
                    "city": zc.city,
                    "state": zc.state,
                    "center_lat": zc.center_lat,
                    "center_lng": zc.center_lng,
                },
            })
        return Response({
            "type": "FeatureCollection",
            "features": features,
        })

    @action(detail=False, methods=["get"])
    def lookup(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        if not lat or not lng:
            return Response(
                {"error": "lat and lng parameters required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {"error": "Invalid lat/lng values"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        matching = ZipCode.objects.filter(
            south__lte=lat, north__gte=lat,
            west__lte=lng, east__gte=lng,
        )
        return Response({
            "count": matching.count(),
            "results": ZipCodeSerializer(matching, many=True).data,
        })


class PropertySnapshotViewSet(viewsets.ModelViewSet):
    queryset = PropertySnapshot.objects.all()
    serializer_class = PropertySnapshotSerializer
    permission_classes = [AllowAny]


class ZipCodeDailyMetricsViewSet(viewsets.ModelViewSet):
    queryset = ZipCodeDailyMetrics.objects.all()
    serializer_class = ZipCodeDailyMetricsSerializer
    permission_classes = [AllowAny]


class MarketReportViewSet(viewsets.ModelViewSet):
    queryset = MarketReport.objects.all()
    serializer_class = MarketReportSerializer
    permission_classes = [AllowAny]


class RentHistoryViewSet(viewsets.ModelViewSet):
    queryset = RentHistory.objects.all()
    serializer_class = RentHistorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        property_id = self.request.query_params.get("property_id")
        if property_id:
            qs = qs.filter(property_id=property_id)
        return qs


class PropertyPhotoViewSet(viewsets.ModelViewSet):
    queryset = PropertyPhoto.objects.all()
    serializer_class = PropertyPhotoSerializer
    permission_classes = [AllowAny]


class ZipCodeRankingViewSet(viewsets.ModelViewSet):
    queryset = ZipCodeRanking.objects.all()
    serializer_class = ZipCodeRankingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(date=date)
        return qs.order_by("-date", "rent_growth_rank")[:50]


class StateDailyMetricsViewSet(viewsets.ModelViewSet):
    queryset = StateDailyMetrics.objects.all()
    serializer_class = StateDailyMetricsSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        return qs.order_by("-date")[:100]


class MarketEventViewSet(viewsets.ModelViewSet):
    queryset = MarketEvent.objects.all()
    serializer_class = MarketEventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        event_type = self.request.query_params.get("event_type")
        posted = self.request.query_params.get("posted_to_linkedin")
        if event_type:
            qs = qs.filter(event_type=event_type)
        if posted is not None:
            qs = qs.filter(posted_to_linkedin=posted.lower() == "true")
        return qs.order_by("-created_at")[:100]


@api_view(["GET"])
def daily_report(request):
    zipcode = request.query_params.get("zipcode")
    if not zipcode:
        return Response(
            {"error": "zipcode parameter required"},
            status=status.HTTP_400_BAD_REQUEST,
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
            status=status.HTTP_404_NOT_FOUND,
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
