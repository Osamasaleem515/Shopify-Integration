from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect, render
from django.contrib import messages
from django import forms
from django.utils.safestring import mark_safe

from .models import Product, ProductDiscount, ProductInventoryLog


class ProductDiscountInline(admin.TabularInline):
    model = ProductDiscount
    extra = 0
    fields = ('name', 'discount_percent', 'active', 'start_date', 'end_date')


class ProductInventoryLogInline(admin.TabularInline):
    model = ProductInventoryLog
    extra = 0
    fields = ('timestamp', 'previous_quantity', 'new_quantity', 'change', 'change_type', 'notes')
    readonly_fields = ('timestamp', 'previous_quantity', 'new_quantity', 'change', 'change_type')
    ordering = ('-timestamp',)
    max_num = 10
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class BulkPriceUpdateForm(forms.Form):
    """
    Form for bulk price update action.
    """
    action_choices = (
        ('increase_percent', 'Increase by percentage'),
        ('decrease_percent', 'Decrease by percentage'),
        ('increase_amount', 'Increase by amount'),
        ('decrease_amount', 'Decrease by amount'),
        ('set_amount', 'Set to specific amount'),
    )
    action = forms.ChoiceField(choices=action_choices)
    value = forms.DecimalField(min_value=0, decimal_places=2)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'inventory_quantity', 'inventory_status',
                   'has_discount', 'updated_at', 'last_inventory_update')
    list_filter = ('updated_at', 'last_inventory_update')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at', 'last_inventory_update')
    inlines = [ProductDiscountInline, ProductInventoryLogInline]
    actions = ['bulk_price_update']
    
    # Custom template with bulk update form
    change_list_template = "admin/products/product/change_list.html"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-price-update/', 
                 self.admin_site.admin_view(self.bulk_price_update_view),
                 name='bulk-price-update'),
        ]
        return custom_urls + urls
    
    def inventory_status(self, obj):
        """
        Display inventory status with color coding.
        """
        if obj.inventory_quantity <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of stock</span>')
        elif obj.inventory_quantity < 10:
            return format_html('<span style="color: orange; font-weight: bold;">Low stock ({})</span>', 
                              obj.inventory_quantity)
        else:
            return format_html('<span style="color: green;">In stock ({})</span>', obj.inventory_quantity)
    
    inventory_status.short_description = 'Inventory Status'
    
    def has_discount(self, obj):
        """
        Check if product has any active discounts.
        """
        active_discounts = obj.discounts.filter(active=True)
        if active_discounts.exists():
            discount = active_discounts.first()
            # Format the decimal value before passing it to format_html
            formatted_value = f"{float(discount.discount_percent):.1f}"
            return format_html('<span style="color: green;">{}</span>', formatted_value + '%')
        return format_html('<span style="color: grey;">No</span>')
    
    has_discount.short_description = 'Discount'
    
    def bulk_price_update(self, request, queryset):
        """
        Custom action for bulk price updates.
        This action redirects to a custom form page.
        """
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        request.session['selected_products'] = [str(pk) for pk in queryset.values_list('pk', flat=True)]
        return redirect('admin:bulk-price-update')
    
    bulk_price_update.short_description = "Update prices in bulk"
    
    def bulk_price_update_view(self, request):
        """
        Custom view for bulk price update form.
        """
        if request.method == 'POST':
            form = BulkPriceUpdateForm(request.POST)
            if form.is_valid():
                action = form.cleaned_data['action']
                value = form.cleaned_data['value']
                
                # Get selected products from the session
                selected_ids = request.session.get('selected_products', [])
                queryset = self.model.objects.filter(id__in=selected_ids)
                
                updated_count = 0
                
                for product in queryset:
                    original_price = product.price
                    new_price = original_price
                    
                    # Apply the selected price change
                    if action == 'increase_percent':
                        new_price = original_price * (1 + (value / 100))
                    elif action == 'decrease_percent':
                        new_price = original_price * (1 - (value / 100))
                    elif action == 'increase_amount':
                        new_price = original_price + value
                    elif action == 'decrease_amount':
                        new_price = max(0, original_price - value)
                    elif action == 'set_amount':
                        new_price = value
                    
                    product.price = new_price
                    product.save()
                    updated_count += 1
                
                # Clear the session
                if 'selected_products' in request.session:
                    del request.session['selected_products']
                
                messages.success(request, f"Successfully updated prices for {updated_count} products.")
                return redirect('admin:products_product_changelist')
                
        else:
            form = BulkPriceUpdateForm()
            # Store selected items in session
            selected = request.GET.getlist('ids')
            if selected:
                request.session['selected_products'] = selected
        
        context = {
            'form': form,
            'selected_count': len(request.session.get('selected_products', [])),
            'title': 'Bulk Price Update',
            'opts': self.model._meta,
        }
        return render(request, 'admin/products/bulk_price_update_form.html', context)
    
    def get_list_filter(self, request):
        """
        Customize list filters.
        """
        return [
            ('updated_at', admin.DateFieldListFilter),
            ('last_inventory_update', admin.DateFieldListFilter),
            'inventory_quantity',
        ]


@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'discount_percent', 'active', 'start_date', 'end_date', 'is_valid')
    list_filter = ('active', 'start_date', 'end_date')
    search_fields = ('name', 'product__name', 'product__sku')
    autocomplete_fields = ['product']


@admin.register(ProductInventoryLog)
class ProductInventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'previous_quantity', 'new_quantity', 'change', 'change_type', 'timestamp')
    list_filter = ('change_type', 'timestamp')
    search_fields = ('product__name', 'product__sku', 'notes')
    readonly_fields = ('timestamp', 'previous_quantity', 'new_quantity', 'change')
    autocomplete_fields = ['product']
    
    def has_add_permission(self, request):
        # Inventory logs should only be created by the system
        return False
