from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import analytics
from .analytics import generate_market_data

router = DefaultRouter()
router.register(r"properties", views.PropertyViewSet)
router.register(r"zipcodes", views.ZipCodeViewSet)
router.register(r"snapshots", views.PropertySnapshotViewSet)
router.register(r"market-reports", views.MarketReportViewSet)
router.register(r"rent-history", views.RentHistoryViewSet)
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
    path("analytics/top-rent-growth/", views.top_rent_growth, name="top-rent-growth"),
    path("analytics/biggest-drops/", views.biggest_rent_drops, name="biggest-rent-drops"),
    path("analytics/inventory-explosion/", views.inventory_explosion, name="inventory-explosion"),
    path("analytics/investor-opportunities/", views.investor_opportunities, name="investor-opportunities"),
    path("analytics/emerging-markets/", views.emerging_markets, name="emerging-markets"),
    path("analytics/hidden-gems/", views.hidden_gems, name="hidden-gems"),
    path("analytics/yield-report/", views.yield_report, name="yield-report"),
    path("analytics/luxury-markets/", views.luxury_markets, name="luxury-markets"),
    path("analytics/top-landlords/", views.top_landlords, name="top-landlords"),
    path("analytics/market-pulse/", views.market_pulse, name="market-pulse"),
    path("analytics/daily-digest/", views.daily_digest, name="daily-digest"),
    path("analytics/rent-history/<str:zipcode>/", views.rent_history_by_zip, name="rent-history-by-zip"),
    path("analytics/opportunity-score/", views.opportunity_score, name="opportunity-score"),
    path("analytics/state-summary/", views.state_summary, name="state-summary"),
    path("analytics/building-performance/", views.building_performance, name="building-performance"),
    path("analytics/daily-report/", views.daily_report, name="daily-report"),
    path("analytics/smart-zip-pick/", views.smart_zip_pick, name="smart-zip-pick"),
    path("analytics/generate-market-data/", generate_market_data, name="generate-market-data"),
    path("analytics/investor-scores/", analytics.investor_scores, name="investor-scores"),
    path("analytics/rental-breakdown/", analytics.rental_breakdown, name="rental-breakdown"),
    path("analytics/growth-metrics/", analytics.growth_metrics, name="growth-metrics"),
    path("analytics/trends/", analytics.trends, name="trends"),
    path("analytics/top-zips/", analytics.top_zips, name="top-zips"),
    path("analytics/rent-drops/", analytics.rent_drops, name="rent-drops"),
]

