from django.urls import path
from . import views

urlpatterns = [
    path("top-rent-growth/", views.top_rent_growth, name="top-rent-growth"),
    path("biggest-drops/", views.biggest_rent_drops, name="biggest-rent-drops"),
    path("inventory-explosion/", views.inventory_explosion, name="inventory-explosion"),
    path("investor-opportunities/", views.investor_opportunities, name="investor-opportunities"),
    path("emerging-markets/", views.emerging_markets, name="emerging-markets"),
    path("hidden-gems/", views.hidden_gems, name="hidden-gems"),
    path("yield-report/", views.yield_report, name="yield-report"),
    path("luxury-markets/", views.luxury_markets, name="luxury-markets"),
    path("top-landlords/", views.top_landlords, name="top-landlords"),
    path("market-pulse/", views.market_pulse, name="market-pulse"),
    path("daily-digest/", views.daily_digest, name="daily-digest"),
    path("rent-history/<str:zipcode>/", views.rent_history_by_zip, name="rent-history-by-zip"),
    path("opportunity-score/", views.opportunity_score, name="opportunity-score"),
    path("state-summary/", views.state_summary, name="state-summary"),
    path("building-performance/", views.building_performance, name="building-performance"),
    path("smart-zip-pick/", views.smart_zip_pick, name="smart-zip-pick"),
    path("generate-market-data/", views.generate_market_data, name="generate-market-data"),
    path("investor-scores/", views.investor_scores, name="investor-scores"),
    path("rental-breakdown/", views.rental_breakdown, name="rental-breakdown"),
    path("growth-metrics/", views.growth_metrics, name="growth-metrics"),
    path("trends/", views.trends, name="trends"),
    path("top-zips/", views.top_zips, name="top-zips"),
    path("rent-drops/", views.rent_drops, name="rent-drops"),
    path("daily-report/", views.daily_report, name="daily-report"),
]
