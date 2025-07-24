import os
import csv
import logging
from datetime import datetime, timedelta

from celery import shared_task, chain
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum, F, Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

import pandas as pd

from .models import Product, ProductInventoryLog

logger = get_task_logger(__name__)


@shared_task
def import_products_from_csv(file_path=None):
    """
    Import products from a CSV file.
    
    Expected CSV format:
    sku,name,price,inventory_quantity,description
    
    Returns a list of dictionaries with imported data.
    """
    logger.info(f"Starting product import from CSV: {file_path}")
    
    # Use a default file path for testing if none provided
    if file_path is None or not os.path.exists(file_path):
        # For testing purposes, use a mock CSV in the project directory
        base_dir = settings.BASE_DIR
        file_path = os.path.join(base_dir, 'products', 'data', 'mock_products.csv')
        
        # Create mock data if file doesn't exist
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create mock data
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['sku', 'name', 'price', 'inventory_quantity', 'description'])
                # Add some sample products
                writer.writerow(['SKU001', 'Test Product 1', '19.99', '100', 'This is a test product'])
                writer.writerow(['SKU002', 'Test Product 2', '29.99', '50', 'Another test product'])
                writer.writerow(['SKU003', 'Test Product 3', '39.99', '25', 'A third test product'])
    
    if not os.path.exists(file_path):
        logger.error(f"CSV file not found: {file_path}")
        return {'status': 'error', 'message': 'CSV file not found', 'imported': 0, 'errors': []}
    
    try:
        # Read CSV using pandas for better handling
        df = pd.read_csv(file_path)
        required_columns = ['sku', 'name', 'price', 'inventory_quantity']
        
        # Check if all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {', '.join(missing_columns)}")
            return {
                'status': 'error', 
                'message': f"Missing required columns: {', '.join(missing_columns)}", 
                'imported': 0, 
                'errors': []
            }
        
        # Clean data and prepare for import
        # Convert price to float
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        # Convert inventory to int
        df['inventory_quantity'] = pd.to_numeric(df['inventory_quantity'], errors='coerce')
        
        # Replace NaN with empty string for string columns
        df['description'] = df['description'].fillna('')
        
        # Filter out rows with invalid data
        valid_data = df.dropna(subset=['sku', 'name', 'price', 'inventory_quantity'])
        
        # Convert to list of dictionaries for further processing
        products_data = valid_data.to_dict('records')
        
        logger.info(f"Found {len(products_data)} valid products in CSV")
        
        return {
            'status': 'success', 
            'message': f"Successfully read {len(products_data)} products from CSV", 
            'data': products_data,
            'file_path': file_path
        }
        
    except Exception as e:
        logger.error(f"Error importing products from CSV: {str(e)}")
        return {
            'status': 'error',
            'message': f"Error importing products: {str(e)}",
            'imported': 0,
            'errors': [str(e)]
        }


@shared_task
def validate_and_update_inventory(import_result):
    """
    Validate imported data and update inventory quantities.
    
    Takes the result from import_products_from_csv task.
    """
    if import_result.get('status') != 'success':
        logger.error(f"Cannot validate and update: Previous task failed with {import_result.get('message')}")
        return import_result
    
    products_data = import_result.get('data', [])
    
    if not products_data:
        logger.info("No products to validate and update")
        return {
            'status': 'success',
            'message': 'No products to validate and update',
            'updated': 0,
            'created': 0,
            'errors': []
        }
    
    logger.info(f"Validating and updating {len(products_data)} products")
    
    updated = 0
    created = 0
    errors = []
    
    try:
        # Process each product
        for item in products_data:
            try:
                sku = item.get('sku')
                name = item.get('name')
                price = item.get('price')
                inventory_quantity = item.get('inventory_quantity', 0)
                description = item.get('description', '')
                
                # Skip invalid data
                if not sku or not name or price is None:
                    errors.append(f"Invalid data for product: {sku}")
                    continue
                
                # Use transaction to ensure consistency
                with transaction.atomic():
                    product, was_created = Product.objects.get_or_create(
                        sku=sku,
                        defaults={
                            'name': name,
                            'price': price,
                            'inventory_quantity': inventory_quantity,
                            'description': description
                        }
                    )
                    
                    if was_created:
                        created += 1
                        # Log initial inventory
                        ProductInventoryLog.objects.create(
                            product=product,
                            previous_quantity=0,
                            new_quantity=inventory_quantity,
                            change_type='import',
                            notes='Initial import'
                        )
                    else:
                        # Only update inventory if it changed
                        if product.inventory_quantity != inventory_quantity:
                            # Create log before updating
                            ProductInventoryLog.objects.create(
                                product=product,
                                previous_quantity=product.inventory_quantity,
                                new_quantity=inventory_quantity,
                                change_type='import',
                                notes='CSV import update'
                            )
                            
                            # Update the product
                            product.inventory_quantity = inventory_quantity
                            product.save()
                            
                        # Always update other fields
                        Product.objects.filter(id=product.id).update(
                            name=name,
                            price=price,
                            description=description
                        )
                        updated += 1
                        
            except Exception as e:
                errors.append(f"Error processing product {item.get('sku')}: {str(e)}")
                logger.error(f"Error processing product {item.get('sku')}: {str(e)}")
                
        # Return results
        result = {
            'status': 'success',
            'message': f"Processed {len(products_data)} products. Created: {created}, Updated: {updated}, Errors: {len(errors)}",
            'created': created,
            'updated': updated,
            'errors': errors,
            'file_path': import_result.get('file_path')
        }
        
        logger.info(f"Inventory update completed. Created: {created}, Updated: {updated}, Errors: {len(errors)}")
        return result
        
    except Exception as e:
        logger.error(f"Error during validation and update: {str(e)}")
        return {
            'status': 'error',
            'message': f"Error during validation and update: {str(e)}",
            'created': created,
            'updated': updated,
            'errors': [str(e)] + errors,
            'file_path': import_result.get('file_path')
        }


@shared_task
def generate_inventory_report(update_result):
    """
    Generate a report summarizing inventory updates and email it.
    
    Takes the result from validate_and_update_inventory task.
    """
    if update_result.get('status') != 'success':
        logger.error(f"Cannot generate report: Previous task failed with {update_result.get('message')}")
        return update_result
    
    logger.info("Generating inventory report")
    
    try:
        # Get stats for the report
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(inventory_quantity__lt=10).count()
        out_of_stock_products = Product.objects.filter(inventory_quantity=0).count()
        
        # Get recent updates (last 24 hours)
        one_day_ago = timezone.now() - timedelta(days=1)
        recent_updates = ProductInventoryLog.objects.filter(
            timestamp__gte=one_day_ago
        ).count()
        
        # Prepare email content
        subject = f"Inventory Update Report - {timezone.now().strftime('%Y-%m-%d')}"
        
        # Report data
        report_data = {
            'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_products': total_products,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'recent_updates': recent_updates,
            'file_processed': update_result.get('file_path'),
            'created': update_result.get('created', 0),
            'updated': update_result.get('updated', 0),
            'errors': update_result.get('errors', [])
        }
        
        # Simple text email for the example
        message = f"""
        Inventory Update Report - {report_data['date']}
        
        Summary:
        - Total Products: {report_data['total_products']}
        - Low Stock Products (<10): {report_data['low_stock_products']}
        - Out of Stock Products: {report_data['out_of_stock_products']}
        - Recent Updates (24h): {report_data['recent_updates']}
        
        CSV Import Results:
        - File Processed: {report_data['file_processed']}
        - New Products Created: {report_data['created']}
        - Products Updated: {report_data['updated']}
        - Errors: {len(report_data['errors'])}
        
        """
        
        # Add error details if any
        if report_data['errors']:
            message += "\nError Details:\n"
            for error in report_data['errors'][:10]:  # Limit to first 10 errors
                message += f"- {error}\n"
            
            if len(report_data['errors']) > 10:
                message += f"... and {len(report_data['errors']) - 10} more errors\n"
        
        # In a real application, we'd use HTML email with proper formatting
        # You could use Django's render_to_string to create an HTML template
        
        # Get recipients from settings or use default
        recipients = getattr(settings, 'INVENTORY_REPORT_RECIPIENTS', ['admin@example.com'])
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com',
            recipient_list=recipients,
            fail_silently=False,
        )
        
        logger.info(f"Inventory report sent to {recipients}")
        
        # Return success
        return {
            'status': 'success',
            'message': f"Report generated and sent to {', '.join(recipients)}",
            'report_data': report_data
        }
        
    except Exception as e:
        logger.error(f"Error generating inventory report: {str(e)}")
        return {
            'status': 'error',
            'message': f"Error generating inventory report: {str(e)}",
            'error': str(e)
        }


@shared_task
def nightly_inventory_update():
    """
    Chain the inventory update tasks together for nightly execution.
    """
    logger.info("Starting nightly inventory update chain")
    
    # Create the task chain
    task_chain = chain(
        import_products_from_csv.s(),
        validate_and_update_inventory.s(),
        generate_inventory_report.s()
    )
    
    # Execute the chain
    return task_chain() 