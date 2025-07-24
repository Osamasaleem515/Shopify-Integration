from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class Product(models.Model):
    """
    Product model for storing product information.
    """
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    inventory_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_inventory_update = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    shopify_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['price']),
            models.Index(fields=['inventory_quantity']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        """
        Override save to update last_inventory_update when inventory quantity changes.
        """
        if self.pk:
            original = Product.objects.get(pk=self.pk)
            if original.inventory_quantity != self.inventory_quantity:
                self.last_inventory_update = timezone.now()
        super().save(*args, **kwargs)


class ProductDiscount(models.Model):
    """
    Model for storing product discounts.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discounts')
    name = models.CharField(max_length=100)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.discount_percent}%)"
    
    @property
    def is_valid(self):
        """
        Check if the discount is currently valid based on dates.
        """
        now = timezone.now()
        if not self.active:
            return False
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True
        
    def get_discounted_price(self, price):
        """
        Calculate the discounted price.
        """
        if not self.is_valid:
            return price
        discount = (price * self.discount_percent) / 100
        return price - discount


class ProductInventoryLog(models.Model):
    """
    Model for logging inventory changes.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    change = models.IntegerField()
    change_type = models.CharField(max_length=50, choices=[
        ('manual', 'Manual Update'),
        ('webhook', 'Webhook Update'),
        ('import', 'CSV Import'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.product.sku}: {self.previous_quantity} → {self.new_quantity}"
    
    def save(self, *args, **kwargs):
        """
        Calculate the change before saving.
        """
        if not self.pk and self.previous_quantity != self.new_quantity:
            self.change = self.new_quantity - self.previous_quantity
        super().save(*args, **kwargs)
