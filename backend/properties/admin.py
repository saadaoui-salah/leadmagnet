import json
import os
import base64
from datetime import date, timedelta
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.contrib import admin
from django.contrib import messages
from django.urls import path
from .models import (
    ZipCode, Property, PropertySnapshot, PropertyUnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    RentHistory, PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
)


class LeadMagnetAdmin(admin.AdminSite):
    site_header = "Lead Magnet Admin"
    site_title = "Lead Magnet"
    index_title = "Dashboard"

    def get_urls(self):
        custom_urls = [
            path("run-zyte/", self.admin_view(self.run_zyte_view), name="run-zyte"),
        ]
        return custom_urls + super().get_urls()

    def index(self, request, extra_context=None):
        today = date.today()
        yesterday = today - timedelta(days=1)

        new_today = Property.objects.filter(first_seen=today).count()

        seen_yesterday = set(
            PropertySnapshot.objects.filter(snapshot_date=yesterday)
            .values_list("property_id", flat=True)
        )
        seen_today = set(
            PropertySnapshot.objects.filter(snapshot_date=today)
            .values_list("property_id", flat=True)
        )
        missing_ids = seen_yesterday - seen_today
        missing_count = len(missing_ids)

        total_properties = Property.objects.count()
        total_snapshots = PropertySnapshot.objects.count()

        stats = {
            "new_today": new_today,
            "missing_count": missing_count,
            "total_properties": total_properties,
            "total_snapshots": total_snapshots,
            "today": today,
            "yesterday": yesterday,
        }

        if extra_context is None:
            extra_context = {}
        extra_context["stats"] = stats

        return super().index(request, extra_context=extra_context)

    def run_zyte_view(self, request):
        if request.method == "POST":
            listing_type = request.POST.get("listing_type", "rent")
            api_key = os.environ.get("ZYTE_API_KEY", "")
            project_id = os.environ.get("ZYTE_PROJECT_ID", "")

            if not api_key:
                messages.error(request, "ZYTE_API_KEY not set in environment")
            elif not project_id:
                messages.error(request, "ZYTE_PROJECT_ID not set in environment")
            else:
                geo = self._fetch_zipcodes()
                if not geo:
                    messages.error(request, "Failed to fetch zipcodes from database")
                else:
                    success, errors = self._submit_jobs(api_key, project_id, geo, listing_type)
                    messages.success(
                        request,
                        f"Zyte spider [{listing_type}]: {success} jobs submitted, {errors} failed"
                    )
            return self.index(request)
        return self.index(request)

    def _fetch_zipcodes(self):
        try:
            zipcodes = ZipCode.objects.all()
            if not zipcodes.exists():
                return None
            return {
                z.zipcode: {"south": z.south, "west": z.west, "north": z.north, "east": z.east}
                for z in zipcodes
            }
        except Exception:
            return None

    def _submit_jobs(self, api_key, project_id, geo, listing_type):
        api_url = "https://app.zyte.com/api/run.json"
        success = 0
        errors = 0
        for zipcode, bounds in geo.items():
            mapbound_json = json.dumps(bounds)
            payload = {
                "project": project_id,
                "spider": "zillow",
                "units": 1,
                "add_tag": f"zillow-{listing_type}-{zipcode}",
                "mapbound": mapbound_json,
                "listing_type": listing_type,
            }

            print(f"[Zyte] Submitting job: project={project_id}, listing_type={listing_type}")
            print(f"[Zyte] mapbound={mapbound_json}")

            auth = base64.b64encode(f"{api_key}:".encode()).decode()
            req = Request(
                api_url,
                data=urlencode(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth}",
                },
                method="POST",
            )

            try:
                with urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                    if result.get("status") == "ok":
                        job_id = result.get("jobid", "unknown")
                        print(f"[Zyte] Job submitted: {job_id}")
                        success += 1
                    else:
                        print(f"[Zyte] Job failed: {result}")
                        errors += 1
            except URLError as e:
                print(f"[Zyte] Request failed: {e}")
                errors += 1
            except Exception as e:
                print(f"[Zyte] Error: {e}")
                errors += 1
        return success, errors


admin_site = LeadMagnetAdmin(name="leadmagnet_admin")


@admin.register(ZipCode, site=admin_site)
class ZipCodeAdmin(admin.ModelAdmin):
    list_display = ["zipcode", "city", "state", "south", "west", "north", "east"]
    search_fields = ["zipcode", "city", "state"]
    list_filter = ["state"]


@admin.register(Property, site=admin_site)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        "zpid", "source", "property_type",
        "street", "city", "state", "zipcode",
        "management_company", "first_seen",
    ]
    list_filter = ["source", "state", "property_type"]
    search_fields = [
        "address", "street", "building_name", "city",
        "management_company",
    ]
    readonly_fields = ["first_seen", "last_seen"]


@admin.register(PropertySnapshot, site=admin_site)
class PropertySnapshotAdmin(admin.ModelAdmin):
    list_display = ["property", "snapshot_date", "status_type", "min_rent", "max_rent"]
    list_filter = ["snapshot_date", "status_type"]
    raw_id_fields = ["property"]


@admin.register(ZipCodeDailyMetrics, site=admin_site)
class ZipCodeDailyMetricsAdmin(admin.ModelAdmin):
    list_display = ["zipcode", "date", "active_listings", "avg_rent", "median_rent"]
    list_filter = ["date"]
    raw_id_fields = ["zipcode"]


@admin.register(MarketReport, site=admin_site)
class MarketReportAdmin(admin.ModelAdmin):
    list_display = ["report_type", "zipcode", "generated_at"]
    list_filter = ["report_type", "generated_at"]
    raw_id_fields = ["zipcode"]


@admin.register(RentHistory, site=admin_site)
class RentHistoryAdmin(admin.ModelAdmin):
    list_display = ["property", "date", "rent", "beds"]
    list_filter = ["date", "beds"]
    raw_id_fields = ["property"]


@admin.register(PropertyPhoto, site=admin_site)
class PropertyPhotoAdmin(admin.ModelAdmin):
    list_display = ["property", "photo_url", "order"]
    raw_id_fields = ["property"]


@admin.register(ZipCodeRanking, site=admin_site)
class ZipCodeRankingAdmin(admin.ModelAdmin):
    list_display = [
        "zipcode", "date",
        "rent_growth_rank", "inventory_rank", "demand_rank",
    ]
    list_filter = ["date"]
    raw_id_fields = ["zipcode"]


@admin.register(StateDailyMetrics, site=admin_site)
class StateDailyMetricsAdmin(admin.ModelAdmin):
    list_display = [
        "state", "date", "avg_rent", "active_listings",
        "rent_change_pct", "property_type",
    ]
    list_filter = ["date", "state", "property_type"]


@admin.register(MarketEvent, site=admin_site)
class MarketEventAdmin(admin.ModelAdmin):
    list_display = [
        "event_type", "zipcode", "title",
        "severity", "posted_to_linkedin", "created_at",
    ]
    list_filter = ["event_type", "severity", "posted_to_linkedin"]
    raw_id_fields = ["zipcode"]
    search_fields = ["title", "description"]
