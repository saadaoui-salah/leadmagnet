from rest_framework import serializers
from .models import (
    ZipCode, Property, Unit, UnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
    PropertyTaxHistory, PropertySchool,
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


class UnitSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitSnapshot
        fields = "__all__"


class UnitSerializer(serializers.ModelSerializer):
    snapshots = UnitSnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = Unit
        fields = "__all__"


class PropertySerializer(serializers.ModelSerializer):
    photos = serializers.SerializerMethodField()
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = "__all__"

    def get_photos(self, obj):
        return PropertyPhotoSerializer(obj.photos.all(), many=True).data


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
    lotId = serializers.CharField(max_length=255)
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
    has_3d_tour = serializers.BooleanField(required=False, default=False)
    has_3d_model = serializers.BooleanField(required=False, default=False)
    description = serializers.CharField(required=False, default="", allow_blank=True)

    def create(self, validated_data):
        property_instance, created = Property.objects.update_or_create(
            zpid=validated_data.get("zpid", ""),
            source=validated_data.get("source", "zillow"),
            defaults=validated_data,
        )
        return property_instance


class PropertyTaxHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyTaxHistory
        fields = "__all__"


class PropertySchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertySchool
        fields = "__all__"
