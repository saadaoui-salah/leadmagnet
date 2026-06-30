import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q


logger = logging.getLogger(__name__)

from .models import (
    ZipCode, Property, Unit, UnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
    PropertyTaxHistory, PropertySchool,
)
from .serializers import (
    ZipCodeSerializer, PropertySerializer, PropertyCreateSerializer,
    UnitSerializer, UnitSnapshotSerializer,
    ZipCodeDailyMetricsSerializer, BuildingDailyMetricsSerializer,
    MarketReportSerializer, PropertyPhotoSerializer,
    ZipCodeRankingSerializer, StateDailyMetricsSerializer, MarketEventSerializer,
    PropertyTaxHistorySerializer, PropertySchoolSerializer,
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

    prop = Property.objects.filter(zpid=str(zpid)).first()
    if not prop:
        return Response({"error": f"Property with zpid {zpid} not found"}, status=status.HTTP_404_NOT_FOUND)

    unit_fields = [
        "bedrooms", "bathrooms", "living_area", "lot_size", "year_built",
        "property_type_detailed", "parking_features", "cooling", "heating",
        "flooring", "appliances", "interior_features", "exterior_features",
        "lot_features", "sewer", "water_source", "architectural_style",
        "garage_spaces", "hoa_fee", "total_fees", "property_tax_rate",
    ]
    list_fields = {"parking_features", "appliances"}
    char_fields = {
        "cooling", "heating", "flooring", "interior_features",
        "exterior_features", "lot_features", "sewer", "water_source",
        "architectural_style", "property_type_detailed", "total_fees",
    }
    float_fields = {"bedrooms", "bathrooms", "lot_size", "garage_spaces", "hoa_fee", "property_tax_rate"}
    int_fields = {"living_area", "year_built"}

    units_data = request.data.get("units", [])

    if units_data:
        for u in units_data:
            unit_id = str(u.get("unit_id", ""))
            if not unit_id:
                continue
            unit, _ = Unit.objects.get_or_create(base=prop, unit_id=unit_id)
            updated = []
            for field in unit_fields:
                if field not in u:
                    continue
                val = u[field]
                current = getattr(unit, field, None)
                if current not in (None, "", [], {}):
                    continue
                if field in list_fields:
                    if isinstance(val, list):
                        setattr(unit, field, val)
                    elif isinstance(val, str):
                        setattr(unit, field, [val] if val else [])
                    else:
                        setattr(unit, field, [])
                elif field in char_fields:
                    if isinstance(val, list):
                        setattr(unit, field, ", ".join(str(v) for v in val))
                    else:
                        setattr(unit, field, str(val))
                elif field in float_fields:
                    try:
                        setattr(unit, field, float(val))
                    except (TypeError, ValueError):
                        continue
                elif field in int_fields:
                    try:
                        setattr(unit, field, int(val))
                    except (TypeError, ValueError):
                        continue
                else:
                    setattr(unit, field, val)
                updated.append(field)
            if "sold_at" in u and u["sold_at"]:
                unit.sold_at = str(u["sold_at"])
                updated.append("sold_at")
            if updated:
                unit.save(update_fields=updated)

            snapshot_fields = {
                "price": u.get("price"),
            }
            snapshot_fields = {k: v for k, v in snapshot_fields.items() if v is not None}
            if snapshot_fields:
                UnitSnapshot.objects.create(unit=unit, **snapshot_fields)
    else:
        unit, _ = Unit.objects.get_or_create(base=prop, unit_id=str(zpid))
        updated_fields = []
        for field in unit_fields:
            if field not in request.data:
                continue
            val = request.data[field]
            current = getattr(unit, field, None)
            if current not in (None, "", [], {}):
                continue
            if field in list_fields:
                if isinstance(val, list):
                    setattr(unit, field, val)
                elif isinstance(val, str):
                    setattr(unit, field, [val] if val else [])
                else:
                    setattr(unit, field, [])
            elif field in char_fields:
                if isinstance(val, list):
                    setattr(unit, field, ", ".join(str(v) for v in val))
                else:
                    setattr(unit, field, str(val))
            elif field in float_fields:
                try:
                    setattr(unit, field, float(val))
                except (TypeError, ValueError):
                    continue
            elif field in int_fields:
                try:
                    setattr(unit, field, int(val))
                except (TypeError, ValueError):
                    continue
            else:
                setattr(unit, field, val)
            updated_fields.append(field)
        if updated_fields:
            unit.save(update_fields=updated_fields)

        snapshot_data = {}
        for key in ["zestimate", "price", "days_on_zillow", "rent_zestimate",
                     "favorite_count", "availability_count", "availability_date",
                     "page_view_count", "time_on_zillow", "listing_sub_type",
                     "ad_targets", "status_type", "status_text"]:
            if key in request.data:
                snapshot_data[key] = request.data[key]
        if snapshot_data:
            UnitSnapshot.objects.create(unit=unit, **snapshot_data)

    description = request.data.get("description")
    if description and not prop.description:
        prop.description = str(description)
        prop.save(update_fields=["description"])

    parcel_id = request.data.get("parcel_id")
    if parcel_id and not prop.parcel_id:
        prop.parcel_id = str(parcel_id)
        prop.save(update_fields=["parcel_id"])

    created = {"tax_history": 0, "schools": 0}

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

    return Response({"status": "ok", "zpid": zpid, "created": created}, status=status.HTTP_200_OK)


@api_view(["GET"])
def property_zpids(request):
    source = request.query_params.get("source", "zillow")
    qs = Property.objects.filter(source=source).exclude(zpid="").values("zpid", "detail_url")
    results = [{"zpid": z["zpid"], "detail_link": z["detail_url"]} for z in qs if z["zpid"] and z["zpid"].isdigit()]
    return Response({"count": len(results), "zpids": results})


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


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.select_related("base").all()
    serializer_class = UnitSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        property_id = self.request.query_params.get("property_id")
        if property_id:
            qs = qs.filter(base_id=property_id)
        return qs


class UnitSnapshotViewSet(viewsets.ModelViewSet):
    queryset = UnitSnapshot.objects.select_related("unit").all()
    serializer_class = UnitSnapshotSerializer
    permission_classes = [AllowAny]


class ZipCodeDailyMetricsViewSet(viewsets.ModelViewSet):
    queryset = ZipCodeDailyMetrics.objects.all()
    serializer_class = ZipCodeDailyMetricsSerializer
    permission_classes = [AllowAny]


class MarketReportViewSet(viewsets.ModelViewSet):
    queryset = MarketReport.objects.all()
    serializer_class = MarketReportSerializer
    permission_classes = [AllowAny]


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
