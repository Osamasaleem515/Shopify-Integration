from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import Product, ProductDiscount, ProductInventoryLog


class ProductAPITestCase(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        
        # Create Product Managers group and add user to it
        self.product_managers_group, created = Group.objects.get_or_create(name='Product Managers')
        self.user.groups.add(self.product_managers_group)
        
        # Give user staff permissions for admin access
        self.user.is_staff = True
        self.user.save()
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            sku='TP1',
            price=Decimal('19.99'),
            inventory_quantity=100,
            description='Test product 1 description'
        )
        self.product2 = Product.objects.create(
            name='Test Product 2',
            sku='TP2',
            price=Decimal('29.99'),
            inventory_quantity=5,
            description='Test product 2 description'
        )
        self.product3 = Product.objects.create(
            name='Different Item',
            sku='DI1',
            price=Decimal('39.99'),
            inventory_quantity=0,
            description='Different item description'
        )
    
    def test_get_products_list(self):
        """
        Test retrieving product list.
        """
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_get_product_detail(self):
        """
        Test retrieving product detail.
        """
        url = reverse('product-detail', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product 1')
        self.assertEqual(response.data['sku'], 'TP1')
    
    def test_create_product(self):
        """
        Test creating a product.
        """
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'sku': 'NP1',
            'price': '49.99',
            'inventory_quantity': 25,
            'description': 'New product description'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 4)
    
    def test_update_product(self):
        """
        Test updating a product.
        """
        url = reverse('product-detail', kwargs={'pk': self.product1.pk})
        data = {
            'name': 'Updated Product 1',
            'sku': 'TP1',
            'price': '24.99',
            'inventory_quantity': 50,
            'description': 'Updated description'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Updated Product 1')
        self.assertEqual(self.product1.price, Decimal('24.99'))
        self.assertEqual(self.product1.inventory_quantity, 50)
    
    def test_delete_product(self):
        """
        Test deleting a product.
        """
        url = reverse('product-detail', kwargs={'pk': self.product3.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_product_filtering(self):
        """
        Test product filtering.
        """
        # Test filtering by name
        url = reverse('product-list') + '?name=Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Test filtering by price range
        url = reverse('product-list') + '?price_min=25.00'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Test filtering by low stock (products with quantity <= 10)
        url = reverse('product-list') + '?low_stock=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # TP2 (qty=5) and DI1 (qty=0)
        # Check that both low stock products are returned
        skus = [item['sku'] for item in response.data['results']]
        self.assertIn('TP2', skus)
        self.assertIn('DI1', skus)
    
    def test_update_inventory(self):
        """
        Test updating inventory via the update_inventory endpoint.
        """
        # For DRF ViewSet actions, the URL name is {basename}-{action_name}
        url = reverse('product-update-inventory', kwargs={'pk': self.product1.pk})
        data = {
            'quantity': 75,
            'notes': 'Manual inventory update test'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.inventory_quantity, 75)
        
        # Check that inventory log was created
        log = ProductInventoryLog.objects.filter(product=self.product1).latest('timestamp')
        self.assertEqual(log.previous_quantity, 100)
        self.assertEqual(log.new_quantity, 75)
        self.assertEqual(log.change_type, 'manual')
        self.assertEqual(log.notes, 'Manual inventory update test')
    
    def test_search_endpoint(self):
        """
        Test the search endpoint.
        """
        url = reverse('product-search') + '?q=Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_insights_endpoint(self):
        """
        Test the insights endpoint.
        """
        url = reverse('product-insights')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_products'], 3)
        self.assertEqual(response.data['low_stock_count'], 2)  # TP2 (qty=5) and DI1 (qty=0)
        self.assertEqual(response.data['out_of_stock_count'], 1)  # DI1 (qty=0)


class ShopifyWebhookTestCase(APITestCase):
    def setUp(self):
        # Create a test product
        self.product = Product.objects.create(
            name='Shopify Product',
            sku='SP1',
            price=Decimal('19.99'),
            inventory_quantity=100,
            description='Shopify test product',
            shopify_id='12345'
        )
    
    def test_webhook_inventory_update(self):
        """
        Test Shopify webhook inventory update.
        """
        url = reverse('shopify-webhook')
        data = {
            'id': '12345',
            'inventory_quantity': 75
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory_quantity, 75)
        
        # Check that inventory log was created
        log = ProductInventoryLog.objects.filter(product=self.product).latest('timestamp')
        self.assertEqual(log.previous_quantity, 100)
        self.assertEqual(log.new_quantity, 75)
        self.assertEqual(log.change_type, 'webhook')
    
    def test_webhook_with_invalid_data(self):
        """
        Test webhook with invalid data.
        """
        url = reverse('shopify-webhook')
        # Missing required field inventory_quantity
        data = {
            'id': '12345'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_webhook_product_not_found(self):
        """
        Test webhook with product not found.
        """
        url = reverse('shopify-webhook')
        data = {
            'id': 'nonexistent',
            'inventory_quantity': 50
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# Add more tests for the Celery tasks
from django.test import TestCase
from .tasks import import_products_from_csv, validate_and_update_inventory, generate_inventory_report
from unittest.mock import patch, MagicMock
import tempfile
import csv
import os

class CeleryTasksTestCase(TestCase):
    def setUp(self):
        # Create a test product
        self.product = Product.objects.create(
            name='Test Task Product',
            sku='TTP1',
            price=Decimal('19.99'),
            inventory_quantity=100,
            description='Test product for tasks'
        )
        
        # Create a temporary CSV file for testing
        self.temp_csv = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        with open(self.temp_csv.name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['sku', 'name', 'price', 'inventory_quantity', 'description'])
            writer.writerow(['TTP1', 'Updated Task Product', '29.99', '150', 'Updated description'])
            writer.writerow(['TTP2', 'New Task Product', '39.99', '200', 'New product description'])
    
    def tearDown(self):
        # Remove temporary file
        os.unlink(self.temp_csv.name)
    
    def test_import_products_from_csv(self):
        """
        Test importing products from CSV.
        """
        result = import_products_from_csv(self.temp_csv.name)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['data']), 2)
    
    def test_validate_and_update_inventory(self):
        """
        Test validating and updating inventory.
        """
        import_result = {
            'status': 'success',
            'data': [
                {
                    'sku': 'TTP1',
                    'name': 'Updated Task Product',
                    'price': 29.99,
                    'inventory_quantity': 150,
                    'description': 'Updated description'
                },
                {
                    'sku': 'TTP2',
                    'name': 'New Task Product',
                    'price': 39.99,
                    'inventory_quantity': 200,
                    'description': 'New product description'
                }
            ],
            'file_path': self.temp_csv.name
        }
        
        result = validate_and_update_inventory(import_result)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['created'], 1)  # One new product
        self.assertEqual(result['updated'], 1)  # One updated product
        
        # Verify product was updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory_quantity, 150)
        self.assertEqual(self.product.price, Decimal('29.99'))
        
        # Verify new product was created
        new_product = Product.objects.get(sku='TTP2')
        self.assertEqual(new_product.name, 'New Task Product')
        self.assertEqual(new_product.inventory_quantity, 200)
    
    @patch('products.tasks.send_mail')
    def test_generate_inventory_report(self, mock_send_mail):
        """
        Test generating inventory report.
        """
        update_result = {
            'status': 'success',
            'created': 1,
            'updated': 1,
            'errors': [],
            'file_path': self.temp_csv.name
        }
        
        result = generate_inventory_report(update_result)
        self.assertEqual(result['status'], 'success')
        mock_send_mail.assert_called_once()
        self.assertTrue('report_data' in result)
        self.assertEqual(result['report_data']['created'], 1)
        self.assertEqual(result['report_data']['updated'], 1)
