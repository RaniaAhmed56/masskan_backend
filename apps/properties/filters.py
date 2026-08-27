import django_filters as filters

from .models import Property


class PropertyFilter(filters.FilterSet):
    """Backs search-results.tsx's filter sidebar 1:1 — every field here
    corresponds to one control in `SearchFilters` (search-sidebar.tsx) on
    the frontend, so that panel can be wired up with zero backend surprises.
    """

    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    bedrooms = filters.NumberFilter(field_name="bedrooms", lookup_expr="gte")
    property_type = filters.ChoiceFilter(choices=Property.PropertyType.choices)
    furnished = filters.ChoiceFilter(choices=Property.Furnished.choices)
    pet_friendly = filters.BooleanFilter()
    near_public_transport = filters.BooleanFilter()
    city = filters.CharFilter(field_name="city", lookup_expr="icontains")
    location = filters.CharFilter(method="filter_location")
    amenities = filters.CharFilter(method="filter_amenities", help_text="Comma-separated amenity keys.")

    class Meta:
        model = Property
        fields = [
            "min_price",
            "max_price",
            "bedrooms",
            "property_type",
            "furnished",
            "pet_friendly",
            "near_public_transport",
            "city",
        ]

    def filter_location(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(Q(city__icontains=value) | Q(area_name__icontains=value) | Q(address__icontains=value))

    def filter_amenities(self, queryset, name, value):
        keys = [k.strip() for k in value.split(",") if k.strip()]
        for key in keys:
            queryset = queryset.filter(amenities__key=key)
        return queryset.distinct()
