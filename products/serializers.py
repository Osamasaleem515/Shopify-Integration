from rest_framework import serializers
from .models import Product, ProductDiscount, ProductInventoryLog


class ProductDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDiscount
        fields = ['id', 'name', 'discount_percent', 'active', 'start_date', 'end_date', 'is_valid']
        read_only_fields = ['is_valid']


class ProductInventoryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventoryLog
        fields = ['id', 'previous_quantity', 'new_quantity', 'change', 'change_type', 'timestamp', 'notes']
        read_only_fields = ['change']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'price', 'inventory_quantity', 'created_at', 
                 'updated_at', 'last_inventory_update', 'description', 'shopify_id']
        read_only_fields = ['created_at', 'updated_at', 'last_inventory_update']


class ProductDetailSerializer(serializers.ModelSerializer):
    discounts = ProductDiscountSerializer(many=True, read_only=True)
    recent_inventory_logs = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'price', 'inventory_quantity', 'created_at', 
                 'updated_at', 'last_inventory_update', 'description', 'shopify_id',
                 'discounts', 'recent_inventory_logs']
        read_only_fields = ['created_at', 'updated_at', 'last_inventory_update']
    
    def get_recent_inventory_logs(self, obj):
        # Get the 5 most recent inventory logs
        logs = obj.inventory_logs.all()[:5]
        return ProductInventoryLogSerializer(logs, many=True).data


class WebhookInventoryUpdateSerializer(serializers.Serializer):
    """
    Serializer for the Shopify inventory webhook payload.
    """
    id = serializers.CharField(required=True)
    sku = serializers.CharField(required=False)
    inventory_quantity = serializers.IntegerField(required=True)
    
    def validate(self, data):
        """
        Validate that we have either id or sku to identify the product.
        """
        if not data.get('id') and not data.get('sku'):
            raise serializers.ValidationError("Either Shopify ID or SKU must be provided")
        return data 