from decimal import Decimal
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from products.models import Product, ProductDiscount, ProductInventoryLog


class Command(BaseCommand):
    help = 'Creates test data for the application'

    def add_arguments(self, parser):
        parser.add_argument('--products', type=int, default=20, help='Number of products to create')
        parser.add_argument('--users', action='store_true', help='Create test users and groups')
        parser.add_argument('--flush', action='store_true', help='Flush existing data before creating new')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing existing data...'))
            ProductInventoryLog.objects.all().delete()
            ProductDiscount.objects.all().delete()
            Product.objects.all().delete()
            
            if options['users']:
                # Don't delete superusers
                User.objects.filter(is_superuser=False).delete()
                Group.objects.all().delete()
        
        # Create products
        self.create_products(options['products'])
        
        # Create users if requested
        if options['users']:
            self.create_users_and_groups()
            
        self.stdout.write(self.style.SUCCESS('Successfully created test data'))
        
    def create_products(self, count):
        """Create test products with discounts and inventory logs."""
        self.stdout.write(f'Creating {count} test products...')
        
        products = []
        for i in range(1, count + 1):
            # Create base product
            product = Product(
                name=f'Test Product {i}',
                sku=f'TP{i:03d}',
                price=Decimal(str(round(random.uniform(9.99, 99.99), 2))),
                inventory_quantity=random.randint(0, 100),
                description=f'This is test product {i} with some description text for testing purposes.',
                shopify_id=f'shopify-{i:05d}' if random.random() > 0.3 else None
            )
            product.save()
            products.append(product)
            
            # Maybe create a discount
            if random.random() > 0.6:
                discount = ProductDiscount(
                    product=product,
                    name=f'Discount for {product.name}',
                    discount_percent=Decimal(str(random.randint(5, 30))),
                    active=random.random() > 0.3,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timezone.timedelta(days=random.randint(1, 30)) if random.random() > 0.5 else None
                )
                discount.save()
            
            # Create some inventory logs
            for _ in range(random.randint(0, 5)):
                prev_qty = random.randint(0, 100)
                new_qty = random.randint(0, 100)
                change_type = random.choice(['manual', 'webhook', 'import'])
                
                log = ProductInventoryLog(
                    product=product,
                    previous_quantity=prev_qty,
                    new_quantity=new_qty,
                    change=new_qty - prev_qty,
                    change_type=change_type,
                    notes=f'Test log for {product.name}',
                    timestamp=timezone.now() - timezone.timedelta(days=random.randint(0, 30))
                )
                log.save()
        
        self.stdout.write(f'Created {len(products)} products')
    
    def create_users_and_groups(self):
        """Create test users and groups with appropriate permissions."""
        self.stdout.write('Creating test users and groups...')
        
        # Create Product Managers group
        product_managers_group, _ = Group.objects.get_or_create(name='Product Managers')
        
        # Add permissions for Product models
        content_types = ContentType.objects.filter(app_label='products')
        permissions = Permission.objects.filter(content_type__in=content_types)
        product_managers_group.permissions.add(*permissions)
        
        # Create API Users group
        api_users_group, _ = Group.objects.get_or_create(name='API Users')
        
        # Add view permissions only
        view_permissions = Permission.objects.filter(
            content_type__in=content_types,
            codename__startswith='view_'
        )
        api_users_group.permissions.add(*view_permissions)
        
        # Create test users
        # Admin user
        admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='adminpass',
            is_staff=True
        )
        admin_user.groups.add(product_managers_group)
        
        # Product manager
        manager = User.objects.create_user(
            username='product_manager',
            email='manager@example.com',
            password='managerpass'
        )
        manager.groups.add(product_managers_group)
        
        # API user
        api_user = User.objects.create_user(
            username='api_user',
            email='api@example.com',
            password='apiuserpass'
        )
        api_user.groups.add(api_users_group)
        
        # Regular user
        User.objects.create_user(
            username='regular_user',
            email='user@example.com',
            password='userpass'
        )
        
        self.stdout.write('Created test users and groups') 