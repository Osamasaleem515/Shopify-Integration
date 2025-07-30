#!/usr/bin/env python
"""
Test script to verify Celery tasks are working correctly.
Run this script to test the task chain manually.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_integration.settings')
django.setup()

from products.tasks import (
    import_products_from_csv,
    validate_and_update_inventory,
    generate_inventory_report,
    nightly_inventory_update
)
from products.models import Product, ProductInventoryLog
from decimal import Decimal

def test_individual_tasks():
    """Test each task individually"""
    print("=== Testing Individual Tasks ===")
    
    # Test Task 1: Import CSV
    print("\n1. Testing CSV Import...")
    result = import_products_from_csv()
    print(f"Import result: {result}")
    
    if result.get('status') == 'success':
        # Test Task 2: Validate and Update
        print("\n2. Testing Validation and Update...")
        update_result = validate_and_update_inventory(result)
        print(f"Update result: {update_result}")
        
        if update_result.get('status') == 'success':
            # Test Task 3: Generate Report
            print("\n3. Testing Report Generation...")
            report_result = generate_inventory_report(update_result)
            print(f"Report result: {report_result}")
    
    print("\n=== Individual Task Testing Complete ===")

def test_task_chain():
    """Test the complete task chain"""
    print("\n=== Testing Complete Task Chain ===")
    
    # Test the full chain
    result = nightly_inventory_update()
    print(f"Chain result: {result}")
    
    print("\n=== Task Chain Testing Complete ===")

def check_database_state():
    """Check the current state of the database"""
    print("\n=== Database State ===")
    
    # Count products
    product_count = Product.objects.count()
    print(f"Total products: {product_count}")
    
    # Count inventory logs
    log_count = ProductInventoryLog.objects.count()
    print(f"Total inventory logs: {log_count}")
    
    # Show recent products
    recent_products = Product.objects.order_by('-created_at')[:5]
    print("\nRecent products:")
    for product in recent_products:
        print(f"  - {product.name} (SKU: {product.sku}, Qty: {product.inventory_quantity})")
    
    print("\n=== Database State Complete ===")

if __name__ == "__main__":
    print("Starting Celery Task Verification...")
    
    # Test individual tasks
    test_individual_tasks()
    
    # Test complete chain
    test_task_chain()
    
    # Check database state
    check_database_state()
    
    print("\nVerification complete!") 