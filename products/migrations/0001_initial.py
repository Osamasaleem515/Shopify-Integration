from django.db import migrations, models
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('inventory_quantity', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_inventory_update', models.DateTimeField(default=django.utils.timezone.now)),
                ('description', models.TextField(blank=True)),
                ('shopify_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'ordering': ['-updated_at'],
                'indexes': [
                    models.Index(fields=['sku'], name='products_pr_sku_58d1ab_idx'),
                    models.Index(fields=['name'], name='products_pr_name_1c2193_idx'),
                    models.Index(fields=['price'], name='products_pr_price_e96e35_idx'),
                    models.Index(fields=['inventory_quantity'], name='products_pr_invento_810e58_idx'),
                    models.Index(fields=['updated_at'], name='products_pr_updated_0e6ed4_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ProductDiscount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('discount_percent', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0)])),
                ('active', models.BooleanField(default=True)),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='discounts', to='products.product')),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='ProductInventoryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_quantity', models.PositiveIntegerField()),
                ('new_quantity', models.PositiveIntegerField()),
                ('change', models.IntegerField()),
                ('change_type', models.CharField(choices=[('manual', 'Manual Update'), ('webhook', 'Webhook Update'), ('import', 'CSV Import')], max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('product', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='inventory_logs', to='products.product')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ] 