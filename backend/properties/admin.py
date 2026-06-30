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
    ZipCode, Property, Unit, UnitSnapshot,
    ZipCodeDailyMetrics, BuildingDailyMetrics, MarketReport,
    PropertyPhoto, ZipCodeRanking,
    StateDailyMetrics, MarketEvent,
)


class LeadMagnetAdmin(admin.AdminSite):
    site_header = "Lead Magnet Admin"
    site_title = "Lead Magnet"
    index_title = "Dashboard"

    def get_urls(self):
        custom_urls = [
            path("run-zyte/", self.admin_view(self.run_zyte_view), name="run-zyte"),
            path("run-zyte-detail/", self.admin_view(self.run_zyte_detail_view), name="run-zyte-detail"),
        ]
        return custom_urls + super().get_urls()

    def index(self, request, extra_context=None):
        today = date.today()

        new_today = Property.objects.filter(first_seen=today).count()
        total_properties = Property.objects.count()
        total_units = Unit.objects.count()
        total_snapshots = UnitSnapshot.objects.count()

        stats = {
            "new_today": new_today,
            "total_properties": total_properties,
            "total_units": total_units,
            "total_snapshots": total_snapshots,
            "today": today,
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

    def run_zyte_detail_view(self, request):
        if request.method == "POST":
            api_key = os.environ.get("ZYTE_DETAIL_API_KEY", "84d09476d2df4b238e0e763b992195d7")
            project_id = os.environ.get("ZYTE_DETAIL_PROJECT_ID", "868681")
            batch_size = int(request.POST.get("batch_size", 2000))
            total = int(request.POST.get("total", 55000))

            if not api_key:
                messages.error(request, "ZYTE_DETAIL_API_KEY not set in environment")
            else:
                success, errors = self._submit_detail_jobs(api_key, project_id, batch_size, total)
                messages.success(
                    request,
                    f"Zyte detail spider: {success} jobs submitted, {errors} failed"
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

    def _submit_detail_jobs(self, api_key, project_id, batch_size, total):
        api_url = "https://app.zyte.com/api/run.json"
        success = 0
        errors = 0
        offsets = range(0, total, batch_size)

        for offset in offsets:
            payload = {
                "project": project_id,
                "spider": "zillow_detail",
                "units": 1,
                "add_tag": f"detail-batch-{offset}",
                "batch": str(batch_size),
                "offset": str(offset),
            }

            print(f"[Zyte Detail] Submitting batch: offset={offset}, batch_size={batch_size}")

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
                        print(f"[Zyte Detail] Job submitted: {job_id}")
                        success += 1
                    else:
                        print(f"[Zyte Detail] Job failed: {result}")
                        errors += 1
            except URLError as e:
                print(f"[Zyte Detail] Request failed: {e}")
                errors += 1
            except Exception as e:
                print(f"[Zyte Detail] Error: {e}")
                errors += 1
            time.sleep(1)
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
        "lotId", "source", "property_type",
        "street", "city", "state", "zipcode",
        "management_company", "first_seen",
    ]
    list_filter = ["source", "state", "property_type"]
    search_fields = [
        "address", "street", "building_name", "city",
        "management_company",
    ]
    readonly_fields = ["first_seen", "last_seen"]


@admin.register(Unit, site=admin_site)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["base", "bedrooms", "bathrooms", "living_area", "year_built"]
    list_filter = ["bedrooms", "bathrooms"]
    raw_id_fields = ["base"]


@admin.register(UnitSnapshot, site=admin_site)
class UnitSnapshotAdmin(admin.ModelAdmin):
    list_display = ["unit", "date", "price", "status_type", "days_on_zillow"]
    list_filter = ["date", "status_type"]
    raw_id_fields = ["unit"]


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
