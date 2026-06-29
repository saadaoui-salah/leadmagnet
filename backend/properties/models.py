from django.db import models


class ZipCode(models.Model):
    zipcode = models.CharField(max_length=10, unique=True, db_index=True)
    city = models.CharField(max_length=255, blank=True, default="")
    state = models.CharField(max_length=10, blank=True, default="")

    # Zillow mapBounds
    south = models.FloatField()
    west = models.FloatField()
    north = models.FloatField()
    east = models.FloatField()

    population = models.IntegerField(null=True, blank=True)
    median_income = models.IntegerField(null=True, blank=True)
    median_home_value = models.IntegerField(null=True, blank=True)

    @property
    def center_lat(self):
        return (self.south + self.north) / 2

    @property
    def center_lng(self):
        return (self.west + self.east) / 2

    @property
    def bbox(self):
        return [self.west, self.south, self.east, self.north]

    def __str__(self):
        return self.zipcode


class Property(models.Model):
    SOURCE_CHOICES = [
        ("zillow", "Zillow"),
        ("realtor", "Realtor"),
        ("redfin", "Redfin"),
        ("other", "Other"),
    ]
    PROPERTY_TYPES = [
        ("apartment", "Apartment"),
        ("house", "House"),
        ("townhome", "Townhome"),
        ("condo", "Condo"),
    ]

    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default="zillow")
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES, blank=True)
    lotId = models.CharField(max_length=255, db_index=True)
    parcel_id = models.CharField(max_length=255, db_index=True)
    detail_url = models.URLField(max_length=500, blank=True, default="")
    building_name = models.CharField(max_length=255, blank=True, default="")
    is_building = models.BooleanField(default=False)
    address = models.TextField(blank=True, default="")
    street = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=255, db_index=True)
    state = models.CharField(max_length=10, db_index=True)
    zipcode = models.CharField(max_length=10, db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    management_company = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    has_3d_tour = models.BooleanField(default=False)
    has_3d_model = models.BooleanField(default=False)
    first_seen = models.DateField(auto_now_add=True)
    last_seen = models.DateField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["zipcode", "city", "state"]),
            models.Index(fields=["property_type"]),
            models.Index(fields=["management_company"]),
        ]

    def __str__(self):
        return self.address
    
class Unit(models.Model):
    base = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")
    unit_id = models.CharField(max_length=255, db_index=True)
    bedrooms = models.FloatField(null=True, blank=True)
    bathrooms = models.FloatField(null=True, blank=True)
    living_area = models.IntegerField(null=True, blank=True)
    sold_at = models.CharField(max_length=500, null=True, blank=True)
    sqft = models.IntegerField(null=True, blank=True)
    lot_size = models.FloatField(null=True, blank=True)
    year_built = models.IntegerField(null=True, blank=True)
    property_type_detailed = models.CharField(max_length=50, blank=True, default="")
    parking_features = models.JSONField(default=list, blank=True)
    cooling = models.CharField(max_length=255, blank=True, default="")
    heating = models.CharField(max_length=255, blank=True, default="")
    flooring = models.CharField(max_length=255, blank=True, default="")
    appliances = models.JSONField(default=list, blank=True)
    interior_features = models.CharField(max_length=500, blank=True, default="")
    exterior_features = models.CharField(max_length=500, blank=True, default="")
    lot_features = models.CharField(max_length=255, blank=True, default="")
    sewer = models.CharField(max_length=255, blank=True, default="")
    water_source = models.CharField(max_length=255, blank=True, default="")
    architectural_style = models.CharField(max_length=255, blank=True, default="")
    garage_spaces = models.FloatField(null=True, blank=True)
    hoa_fee = models.FloatField(null=True, blank=True)
    total_fees = models.CharField(max_length=100, blank=True, default="")
    property_tax_rate = models.FloatField(null=True, blank=True)

class UnitSnapshot(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="snapshots")
    zestimate = models.IntegerField(null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    days_on_zillow = models.IntegerField(null=True, blank=True)
    rent_zestimate = models.IntegerField(null=True, blank=True)
    favorite_count = models.IntegerField(null=True, blank=True)
    availability_count = models.IntegerField(null=True, blank=True)
    availability_date = models.CharField(max_length=50, blank=True, default="")
    page_view_count = models.IntegerField(null=True, blank=True)
    time_on_zillow = models.CharField(max_length=50, blank=True, default="")
    listing_sub_type = models.JSONField(default=list, blank=True)
    ad_targets = models.JSONField(default=dict, blank=True)
    status_type = models.CharField(max_length=100, blank=True, default="")
    status_text = models.CharField(max_length=255, blank=True, default="")




class ZipCodeDailyMetrics(models.Model):
    zipcode = models.ForeignKey(ZipCode, on_delete=models.CASCADE, related_name="daily_metrics")
    date = models.DateField(db_index=True)
    active_listings = models.IntegerField(default=0)
    avg_rent = models.FloatField(null=True, blank=True)
    median_rent = models.FloatField(null=True, blank=True)
    avg_studio_rent = models.FloatField(null=True, blank=True)
    avg_1br_rent = models.FloatField(null=True, blank=True)
    avg_2br_rent = models.FloatField(null=True, blank=True)
    avg_3br_rent = models.FloatField(null=True, blank=True)
    rent_change_pct = models.FloatField(null=True, blank=True)
    inventory_change_pct = models.FloatField(null=True, blank=True)
    new_listings = models.IntegerField(default=0)
    removed_listings = models.IntegerField(default=0)
    luxury_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("zipcode", "date")


class BuildingDailyMetrics(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="building_metrics")
    date = models.DateField(db_index=True)
    avg_rent = models.FloatField(null=True, blank=True)
    availability_count = models.IntegerField(default=0)
    rent_change_pct = models.FloatField(null=True, blank=True)
    inventory_change_pct = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("property", "date")


class MarketReport(models.Model):
    REPORT_TYPES = [
        ("rent_growth", "Rent Growth"),
        ("rent_drop", "Rent Drop"),
        ("inventory", "Inventory"),
        ("heatmap", "Heatmap"),
        ("investor", "Investor"),
        ("social", "Social Media"),
    ]

    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    zipcode = models.ForeignKey(ZipCode, null=True, blank=True, on_delete=models.SET_NULL)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)

    def __str__(self):
        return self.report_type


class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="photos")
    photo_url = models.URLField(max_length=500)
    caption = models.CharField(max_length=255, blank=True, default="")
    order = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["property", "order"]),
        ]


class ZipCodeRanking(models.Model):
    zipcode = models.ForeignKey(ZipCode, on_delete=models.CASCADE, related_name="rankings")
    date = models.DateField()
    rent_growth_rank = models.IntegerField(null=True, blank=True)
    inventory_rank = models.IntegerField(null=True, blank=True)
    demand_rank = models.IntegerField(null=True, blank=True)
    avg_rent_rank = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("zipcode", "date")
        indexes = [
            models.Index(fields=["date", "rent_growth_rank"]),
            models.Index(fields=["date", "inventory_rank"]),
        ]

    def __str__(self):
        return f"{self.zipcode} - {self.date}"


class StateDailyMetrics(models.Model):
    state = models.CharField(max_length=10)
    date = models.DateField()
    avg_rent = models.FloatField(null=True, blank=True)
    median_rent = models.FloatField(null=True, blank=True)
    active_listings = models.IntegerField(default=0)
    rent_change_pct = models.FloatField(null=True, blank=True)
    inventory_change_pct = models.FloatField(null=True, blank=True)
    property_type = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        unique_together = ("state", "date", "property_type")
        indexes = [
            models.Index(fields=["state", "date"]),
        ]

    def __str__(self):
        return f"{self.state} - {self.date}"


class MarketEvent(models.Model):
    EVENT_TYPES = [
        ("inventory_up", "Inventory Up"),
        ("inventory_down", "Inventory Down"),
        ("rent_drop", "Rent Drop"),
        ("rent_surge", "Rent Surge"),
        ("new_construction", "New Construction"),
        ("luxury_launch", "Luxury Launch"),
        ("market_heat", "Market Heat"),
        ("market_cool", "Market Cool"),
        ("other", "Other"),
    ]

    zipcode = models.ForeignKey(ZipCode, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    severity = models.IntegerField(default=1, help_text="1=info, 2=notable, 3=significant")
    created_at = models.DateTimeField(auto_now_add=True)
    posted_to_linkedin = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["zipcode", "event_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["posted_to_linkedin"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.zipcode}"



class PropertyTaxHistory(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="tax_history")
    date = models.DateField()
    tax_amount = models.IntegerField()
    value = models.IntegerField()
    year = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["property", "date"]),
            models.Index(fields=["year"]),
        ]

    def __str__(self):
        return f"{self.property} - {self.year} - ${self.tax_amount}"


class PropertySchool(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="schools")
    name = models.CharField(max_length=255)
    rating = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=50, blank=True, default="")
    level = models.CharField(max_length=50, blank=True, default="")
    grades = models.CharField(max_length=50, blank=True, default="")
    students_count = models.IntegerField(null=True, blank=True)
    teacher_count = models.IntegerField(null=True, blank=True)
    student_teacher_ratio = models.FloatField(null=True, blank=True)
    distance = models.FloatField(null=True, blank=True)
    is_assigned = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["property", "rating"]),
            models.Index(fields=["level"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.rating}/10) - {self.property}"
