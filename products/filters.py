import django_filters
from django.db.models import Q
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Filter for Product model.
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    sku = django_filters.CharFilter(lookup_expr='icontains')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    quantity_min = django_filters.NumberFilter(field_name='inventory_quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='inventory_quantity', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')

    class Meta:
        model = Product
        fields = ['name', 'sku', 'price_min', 'price_max', 'quantity_min', 'quantity_max',
                  'updated_after', 'updated_before', 'low_stock', 'has_discount']
    
    def filter_low_stock(self, queryset, name, value):
        """
        Filter for products with low stock (less than 10 items).
        """
        if value:
            return queryset.filter(inventory_quantity__lt=10)
        return queryset
    
    def filter_has_discount(self, queryset, name, value):
        """
        Filter for products that have active discounts.
        """
        if value:
            # Find products with active discounts
            return queryset.filter(discounts__active=True).distinct()
        return queryset 