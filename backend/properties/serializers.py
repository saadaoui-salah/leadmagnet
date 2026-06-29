from rest_framework import serializers
from .models import (
    ZipCode, Property, PropertySnapshot, PropertyUnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    RentHistory, PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
    PropertyPriceHistory, PropertyTaxHistory, PropertySchool,
)


class ZipCodeSerializer(serializers.ModelSerializer):
    center_lat = serializers.FloatField(read_only=True)
    center_lng = serializers.FloatField(read_only=True)
    bbox = serializers.ListField(read_only=True)

    class Meta:
        model = ZipCode
        fields = [
            "id", "zipcode", "city", "state",
            "south", "west", "north", "east",
            "population", "median_income", "median_home_value",
            "center_lat", "center_lng", "bbox",
        ]


class PropertySerializer(serializers.ModelSerializer):
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = "__all__"

    def get_photos(self, obj):
        return PropertyPhotoSerializer(obj.photos.all(), many=True).data


class PropertySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertySnapshot
        fields = "__all__"


class PropertyUnitSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyUnitSnapshot
        fields = "__all__"


class ZipCodeDailyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZipCodeDailyMetrics
        fields = "__all__"


class BuildingDailyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingDailyMetrics
        fields = "__all__"


class MarketReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketReport
        fields = "__all__"


class RentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RentHistory
        fields = "__all__"


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = "__all__"


class ZipCodeRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZipCodeRanking
        fields = "__all__"


class StateDailyMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateDailyMetrics
        fields = "__all__"


class MarketEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketEvent
        fields = "__all__"


class PropertyCreateSerializer(serializers.Serializer):
    source = serializers.ChoiceField(
        choices=Property.SOURCE_CHOICES, default="zillow"
    )
    zpid = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    detail_url = serializers.CharField(max_length=500, required=False, default="", allow_blank=True)
    building_name = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    is_building = serializers.BooleanField(required=False, default=False)
    address = serializers.CharField(required=False, default="", allow_blank=True)
    street = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    city = serializers.CharField(max_length=255)
    state = serializers.CharField(max_length=10)
    zipcode = serializers.CharField(max_length=10)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    property_type = serializers.ChoiceField(
        choices=Property.PROPERTY_TYPES, required=False, default="", allow_blank=True
    )
    management_company = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    primary_photo = serializers.CharField(max_length=500, required=False, default="", allow_blank=True)

    snapshot = serializers.DictField(required=False, default=dict)

    def create(self, validated_data):
        snapshot_data = validated_data.pop("snapshot", {})

        property_instance, created = Property.objects.update_or_create(
            zpid=validated_data.get("zpid", ""),
            source=validated_data.get("source", "zillow"),
            defaults=validated_data,
        )

        photo_urls = snapshot_data.pop("photo_urls", [])

        if snapshot_data:
            PropertySnapshot.objects.update_or_create(
                property=property_instance,
                snapshot_date=snapshot_data.get("snapshot_date", property_instance.last_seen),
                defaults={
                    "status_type": snapshot_data.get("status_type", ""),
                    "status_text": snapshot_data.get("status_text", ""),
                    "min_rent": snapshot_data.get("min_rent"),
                    "max_rent": snapshot_data.get("max_rent"),
                    "availability_count": snapshot_data.get("availability_count"),
                    "availability_date": snapshot_data.get("availability_date", ""),
                    "has_3d_model": snapshot_data.get("has_3d_model", False),
                    "is_featured_listing": snapshot_data.get("is_featured_listing", False),
                    "days_on_zillow": snapshot_data.get("days_on_zillow"),
                    "rent_zestimate": snapshot_data.get("rent_zestimate"),
                },
            )

            units_data = snapshot_data.get("units", [])
            if units_data:
                snap = PropertySnapshot.objects.get(
                    property=property_instance,
                    snapshot_date=snapshot_data.get("snapshot_date", property_instance.last_seen),
                )
                snap.units.all().delete()
                for u in units_data:
                    PropertyUnitSnapshot.objects.create(
                        property_snapshot=snap,
                        beds=u.get("beds"),
                        price=u.get("price"),
                        room_for_rent=u.get("room_for_rent", False),
                    )

        if photo_urls:
            property_instance.photos.all().delete()
            for i, url in enumerate(photo_urls):
                PropertyPhoto.objects.create(
                    property=property_instance,
                    photo_url=url,
                    order=i,
                )
            if not property_instance.primary_photo:
                property_instance.primary_photo = photo_urls[0]
                property_instance.save(update_fields=["primary_photo"])

        return property_instance


class PropertyPriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPriceHistory
        fields = "__all__"


class PropertyTaxHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyTaxHistory
        fields = "__all__"


class PropertySchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertySchool
        fields = "__all__"
