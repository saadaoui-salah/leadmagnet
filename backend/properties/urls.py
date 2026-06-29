from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"properties", views.PropertyViewSet)
router.register(r"zipcodes", views.ZipCodeViewSet)
router.register(r"units", views.UnitViewSet)
router.register(r"unit-snapshots", views.UnitSnapshotViewSet)
router.register(r"market-reports", views.MarketReportViewSet)
router.register(r"photos", views.PropertyPhotoViewSet)
router.register(r"zip-rankings", views.ZipCodeRankingViewSet)
router.register(r"state-metrics", views.StateDailyMetricsViewSet)
router.register(r"market-events", views.MarketEventViewSet)

urlpatterns = [
    path("properties/zpids/", views.property_zpids, name="property-zpids"),
    path("", include(router.urls)),
    path("ingest/", views.receive_listing, name="receive-listing"),
    path("ingest/bulk/", views.receive_listings_bulk, name="receive-listings-bulk"),
    path("ingest/detail/", views.receive_property_detail, name="receive-property-detail"),
    path("stats/", views.property_stats, name="property-stats"),
]
