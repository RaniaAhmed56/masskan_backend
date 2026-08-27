"""Populate the database with realistic demo data covering every app.

Run with:

    python manage.py seed_demo_data

Safe to re-run — everything is created with `get_or_create`/`update_or_create`
keyed on a natural unique field, so running it twice does not duplicate rows.
This does NOT attach real image files to properties/avatars (that would
require shipping binary fixtures); `primary_image` will simply be null for
seeded listings, which the frontend already handles via its fallback image
component.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.areas.models import Area, AreaReview, NearbyPlace
from apps.messaging.models import Conversation
from apps.notifications.models import Notification
from apps.properties.models import Amenity, Property
from apps.reviews.models import LandlordReview, PropertyReview
from apps.scheduling.models import VisitRequest
from apps.subscriptions.models import PlanFeature, SubscriptionPlan

User = get_user_model()

AMENITIES = [
    ("wifi", "WiFi"),
    ("parking", "Parking"),
    ("gym", "Gym"),
    ("pool", "Swimming Pool"),
    ("elevator", "Elevator"),
    ("balcony", "Balcony"),
    ("air_conditioning", "Air Conditioning"),
    ("security", "24/7 Security"),
    ("laundry", "Laundry"),
    ("pet_friendly_space", "Pet-Friendly Space"),
    ("garden", "Garden"),
    ("storage", "Storage Room"),
]

AREAS = [
    {
        "name": "Downtown District",
        "city": "Cairo",
        "safety": 82,
        "quietness": 55,
        "amenities_score": 90,
        "transport": 95,
        "schools": 70,
        "entertainment": 92,
        "family_friendly_score": 60,
        "student_friendly_score": 85,
        "price_level": Area.PriceLevel.HIGH,
        "avg_price_min": 1000,
        "avg_price_max": 1800,
        "demand_trend": "+12% demand growth this month",
        "places": [
            ("Metro Station", NearbyPlace.Category.TRANSPORT, "5 min walk"),
            ("Central Mall", NearbyPlace.Category.SHOPPING, "10 min walk"),
            ("City Hospital", NearbyPlace.Category.HEALTHCARE, "8 min drive"),
        ],
    },
    {
        "name": "Green Valley Suburbs",
        "city": "Cairo",
        "safety": 91,
        "quietness": 88,
        "amenities_score": 70,
        "transport": 60,
        "schools": 88,
        "entertainment": 55,
        "family_friendly_score": 95,
        "student_friendly_score": 50,
        "price_level": Area.PriceLevel.MODERATE,
        "avg_price_min": 700,
        "avg_price_max": 1200,
        "demand_trend": "+6% demand growth this month",
        "places": [
            ("Green Valley Elementary", NearbyPlace.Category.EDUCATION, "3 min walk"),
            ("Community Park", NearbyPlace.Category.RECREATION, "5 min walk"),
            ("Family Clinic", NearbyPlace.Category.HEALTHCARE, "10 min walk"),
        ],
    },
    {
        "name": "University Quarter",
        "city": "Giza",
        "safety": 75,
        "quietness": 60,
        "amenities_score": 80,
        "transport": 85,
        "schools": 96,
        "entertainment": 78,
        "family_friendly_score": 55,
        "student_friendly_score": 98,
        "price_level": Area.PriceLevel.LOW,
        "avg_price_min": 400,
        "avg_price_max": 750,
        "demand_trend": "+20% demand growth this month",
        "places": [
            ("State University", NearbyPlace.Category.EDUCATION, "2 min walk"),
            ("Student Bookstore", NearbyPlace.Category.SHOPPING, "4 min walk"),
            ("Bus Terminal", NearbyPlace.Category.TRANSPORT, "6 min walk"),
        ],
    },
]

SELLER_PLANS = [
    {
        "name": "Free", "price": 0, "icon": "Rocket", "description": "Perfect for getting started",
        "max_active_listings": 1, "features": [
            ("1 active listing", True), ("Basic visibility", True), ("Tenant messaging", True),
            ("Featured badge", False), ("Priority support", False), ("Analytics", False),
        ],
    },
    {
        "name": "Basic", "price": 49, "icon": "Star", "description": "Best for active landlords", "popular": True,
        "max_active_listings": 5, "features": [
            ("5 active listings", True), ("Enhanced visibility", True), ("Priority messaging", True),
            ("Basic analytics", True), ("Email support", True), ("Featured badge", False),
        ],
    },
    {
        "name": "Professional", "price": 99, "icon": "Crown", "description": "For serious investors",
        "max_active_listings": 15, "features": [
            ("15 active listings", True), ("Premium visibility", True), ("Featured badges", True),
            ("Advanced analytics", True), ("Priority support", True), ("Verified badge", True),
        ],
    },
    {
        "name": "Premium", "price": 199, "icon": "Gem", "description": "For property managers",
        "max_active_listings": None, "features": [
            ("50+ listings", True), ("Top search ranking", True), ("Multiple featured badges", True),
            ("Full analytics suite", True), ("24/7 priority support", True), ("Account manager", True),
        ],
    },
]

BUYER_PLANS = [
    {
        "name": "Free", "price": 0, "icon": "Search", "description": "Basic apartment hunting",
        "max_saved_properties": 10, "max_landlord_contacts_per_month": 0, "features": [
            ("Browse all listings", True), ("Save up to 10 apartments", True), ("Basic search filters", True),
            ("Contact landlords", False), ("AI recommendations", False), ("Advanced analytics", False),
        ],
    },
    {
        "name": "Basic", "price": 19, "icon": "Smartphone", "description": "Enhanced search features", "popular": True,
        "max_saved_properties": 50, "max_landlord_contacts_per_month": 5, "has_ai_matching": True, "features": [
            ("Browse all listings", True), ("Save up to 50 apartments", True), ("Advanced search filters", True),
            ("Contact landlords (5/month)", True), ("Basic AI search", True), ("Saved searches", True),
        ],
    },
    {
        "name": "Pro", "price": 39, "icon": "Bot", "description": "AI-powered matching",
        "max_saved_properties": None, "max_landlord_contacts_per_month": None, "has_ai_matching": True, "features": [
            ("Browse all listings", True), ("Unlimited saved apartments", True), ("Advanced filters + sorting", True),
            ("Unlimited landlord contact", True), ("Advanced AI matching", True), ("Personal recommendations", True),
        ],
    },
    {
        "name": "Premium", "price": 59, "icon": "Sparkles", "description": "VIP treatment",
        "max_saved_properties": None, "max_landlord_contacts_per_month": None, "has_ai_matching": True,
        "has_priority_support": True, "features": [
            ("Everything in Pro", True), ("VIP support line", True), ("Early access to new listings", True),
            ("Dedicated relocation advisor", True), ("Priority visit scheduling", True), ("Verified badge", True),
        ],
    },
]

PROPERTY_SEEDS = [
    {
        "title": "Elegant Modern Apartment", "property_type": Property.PropertyType.APARTMENT,
        "price": 1200, "bedrooms": 2, "bathrooms": 2, "area_sqft": 850,
        "address": "123 Main Street, Downtown District", "city": "Cairo", "area_name": "Downtown District",
        "furnished": Property.Furnished.FURNISHED, "pet_friendly": True, "near_public_transport": True,
        "is_featured": True, "amenities": ["wifi", "gym", "elevator", "air_conditioning", "security"],
    },
    {
        "title": "Cozy Family Villa", "property_type": Property.PropertyType.VILLA,
        "price": 2200, "bedrooms": 4, "bathrooms": 3, "area_sqft": 2100,
        "address": "45 Maple Avenue, Green Valley Suburbs", "city": "Cairo", "area_name": "Green Valley Suburbs",
        "furnished": Property.Furnished.UNFURNISHED, "pet_friendly": True, "near_public_transport": False,
        "is_featured": True, "amenities": ["parking", "garden", "security", "storage"],
    },
    {
        "title": "Bright Studio Near Campus", "property_type": Property.PropertyType.STUDIO,
        "price": 480, "bedrooms": 1, "bathrooms": 1, "area_sqft": 400,
        "address": "9 College Road, University Quarter", "city": "Giza", "area_name": "University Quarter",
        "furnished": Property.Furnished.SEMI, "pet_friendly": False, "near_public_transport": True,
        "is_featured": False, "amenities": ["wifi", "laundry", "air_conditioning"],
    },
    {
        "title": "Skyline Penthouse Suite", "property_type": Property.PropertyType.PENTHOUSE,
        "price": 3500, "bedrooms": 3, "bathrooms": 3, "area_sqft": 1800,
        "address": "1 Tower Plaza, Downtown District", "city": "Cairo", "area_name": "Downtown District",
        "furnished": Property.Furnished.FURNISHED, "pet_friendly": False, "near_public_transport": True,
        "is_featured": True, "amenities": ["pool", "gym", "elevator", "security", "balcony"],
    },
    {
        "title": "Quiet Suburban Townhouse", "property_type": Property.PropertyType.TOWNHOUSE,
        "price": 950, "bedrooms": 3, "bathrooms": 2, "area_sqft": 1300,
        "address": "22 Willow Lane, Green Valley Suburbs", "city": "Cairo", "area_name": "Green Valley Suburbs",
        "furnished": Property.Furnished.UNFURNISHED, "pet_friendly": True, "near_public_transport": False,
        "is_featured": False, "amenities": ["parking", "garden"],
        "status": Property.Status.PENDING,
    },
]


class Command(BaseCommand):
    help = "Seeds the database with demo users, properties, areas, plans, reviews, and activity."

    @transaction.atomic
    def handle(self, *args, **options):
        amenities = self._seed_amenities()
        areas = self._seed_areas()
        admin, landlords, searchers = self._seed_users()
        properties = self._seed_properties(landlords, amenities)
        self._seed_plans()
        self._seed_reviews(properties, landlords, searchers)
        self._seed_area_reviews(areas, searchers)
        self._seed_activity(properties, landlords, searchers)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write(f"  Admin login:    {admin.email} / demo12345")
        self.stdout.write(f"  Landlord login: {landlords[0].email} / demo12345")
        self.stdout.write(f"  Searcher login: {searchers[0].email} / demo12345")

    def _seed_amenities(self):
        amenities = {}
        for key, label in AMENITIES:
            amenity, _ = Amenity.objects.get_or_create(key=key, defaults={"label": label})
            amenities[key] = amenity
        return amenities

    def _seed_areas(self):
        areas = {}
        for spec in AREAS:
            places = spec.pop("places")
            area, _ = Area.objects.update_or_create(name=spec["name"], defaults=spec)
            for name, category, distance in places:
                NearbyPlace.objects.get_or_create(
                    area=area, name=name, defaults={"category": category, "distance_label": distance}
                )
            areas[area.name] = area
            spec["places"] = places  # restore, in case handle() ever re-reads AREAS
        return areas

    def _seed_users(self):
        admin, created = User.objects.get_or_create(
            email="admin@masskan.app",
            defaults={"username": "admin", "is_staff": True, "is_superuser": True, "role": User.Role.BOTH},
        )
        if created:
            admin.set_password("demo12345")
            admin.save()

        landlord_specs = [
            ("sarah.landlord@masskan.app", "Sarah", "Johnson", "Sunrise Properties LLC", 120),
            ("michael.landlord@masskan.app", "Michael", "Chen", "Chen Realty Group", 60),
        ]
        landlords = []
        for email, first, last, company, response_time in landlord_specs:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "first_name": first,
                    "last_name": last,
                    "role": User.Role.LANDLORD,
                    "company_name": company,
                    "response_time_minutes": response_time,
                    "is_email_verified": True,
                    "verification_status": User.VerificationStatus.VERIFIED,
                },
            )
            if created:
                user.set_password("demo12345")
                user.save()
            landlords.append(user)

        searcher_specs = [
            ("amira.searcher@masskan.app", "Amira", "Hassan"),
            ("omar.searcher@masskan.app", "Omar", "Farouk"),
        ]
        searchers = []
        for email, first, last in searcher_specs:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "first_name": first,
                    "last_name": last,
                    "role": User.Role.SEARCHER,
                    "is_email_verified": True,
                },
            )
            if created:
                user.set_password("demo12345")
                user.save()
            searchers.append(user)

        return admin, landlords, searchers

    def _seed_properties(self, landlords, amenities):
        properties = []
        for i, spec in enumerate(PROPERTY_SEEDS):
            spec = dict(spec)
            amenity_keys = spec.pop("amenities")
            status = spec.pop("status", Property.Status.ACTIVE)
            owner = landlords[i % len(landlords)]

            property_obj, _ = Property.objects.update_or_create(
                title=spec["title"],
                owner=owner,
                defaults={
                    **spec,
                    "status": status,
                    "description": (
                        f"A wonderful {spec['bedrooms']}-bedroom {spec['property_type']} in "
                        f"{spec['area_name']}, {spec['city']}. Ready for move-in."
                    ),
                    "available_from": date.today() + timedelta(days=7),
                    "lease_term_months": 12,
                },
            )
            property_obj.amenities.set([amenities[k] for k in amenity_keys])
            properties.append(property_obj)
        return properties

    def _seed_plans(self):
        for role, plans in ((SubscriptionPlan.Role.LANDLORD, SELLER_PLANS), (SubscriptionPlan.Role.SEARCHER, BUYER_PLANS)):
            for order, spec in enumerate(plans):
                features = spec.pop("features")
                popular = spec.pop("popular", False)
                slug = f"{role}-{spec['name'].lower()}"
                plan, _ = SubscriptionPlan.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "role": role,
                        "name": spec["name"],
                        "price_monthly": spec["price"],
                        "description": spec["description"],
                        "icon": spec["icon"],
                        "is_popular": popular,
                        "sort_order": order,
                        "max_active_listings": spec.get("max_active_listings"),
                        "max_saved_properties": spec.get("max_saved_properties"),
                        "max_landlord_contacts_per_month": spec.get("max_landlord_contacts_per_month"),
                        "has_ai_matching": spec.get("has_ai_matching", False),
                        "has_priority_support": spec.get("has_priority_support", False),
                    },
                )
                plan.features.all().delete()
                for order2, (text, included) in enumerate(features):
                    PlanFeature.objects.create(plan=plan, text=text, included=included, order=order2)

    def _seed_reviews(self, properties, landlords, searchers):
        for property_obj in properties[:3]:
            for i, searcher in enumerate(searchers):
                PropertyReview.objects.update_or_create(
                    property=property_obj,
                    user=searcher,
                    defaults={
                        "rating": 4 + (i % 2),
                        "title": "Great place to live",
                        "comment": "Responsive landlord, clean building, exactly as described.",
                    },
                )
        for landlord in landlords:
            for searcher in searchers:
                LandlordReview.objects.update_or_create(
                    landlord=landlord,
                    reviewer=searcher,
                    defaults={"rating": 5, "comment": "Professional, quick to respond, highly recommended."},
                )

    def _seed_area_reviews(self, areas, searchers):
        for area in areas.values():
            for i, searcher in enumerate(searchers):
                AreaReview.objects.update_or_create(
                    area=area,
                    user=searcher,
                    defaults={"rating": 4 + (i % 2), "comment": f"Lived near {area.name} for a year — great spot."},
                )

    def _seed_activity(self, properties, landlords, searchers):
        # A sample conversation with a couple of messages.
        conversation, _ = Conversation.objects.get_or_create(
            property=properties[0], initiator=searchers[0], recipient=properties[0].owner
        )
        if not conversation.messages.exists():
            conversation.messages.create(
                sender=searchers[0], text="Hi! Is this apartment still available for viewing this week?"
            )
            conversation.messages.create(
                sender=properties[0].owner, text="Yes, it is! I have openings Thursday and Friday afternoon."
            )

        # A sample visit request.
        VisitRequest.objects.get_or_create(
            property=properties[0],
            requester=searchers[0],
            visit_date=date.today() + timedelta(days=3),
            defaults={
                "full_name": searchers[0].full_name,
                "email": searchers[0].email,
                "phone": "+20 100 000 0000",
                "visit_time": "14:00",
                "notes": "Looking forward to seeing the place!",
                "status": VisitRequest.Status.PENDING,
            },
        )

        # A sample notification for the first landlord.
        Notification.objects.get_or_create(
            user=landlords[0],
            type=Notification.NotificationType.SYSTEM,
            message="Welcome to Masskan! Complete your landlord profile to start listing.",
            defaults={"link": "/profile"},
        )
