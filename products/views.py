from django.db import transaction
from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, FloatField, Q
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

import django_filters.rest_framework
import numpy as np

# Import these conditionally to allow migrations to run
# These will be imported when the view functions that need them are called
SENTENCE_TRANSFORMER_IMPORT_ERROR = None
SPACY_IMPORT_ERROR = None

try:
    import spacy
except ImportError as e:
    SPACY_IMPORT_ERROR = str(e)
    spacy = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    SENTENCE_TRANSFORMER_IMPORT_ERROR = str(e)
    SentenceTransformer = None

from django.core.cache import cache

from .models import Product, ProductDiscount, ProductInventoryLog
from .serializers import (
    ProductSerializer, ProductDetailSerializer, ProductDiscountSerializer,
    WebhookInventoryUpdateSerializer
)
from .filters import ProductFilter
from .permissions import IsInProductManagerGroup, IsAdminUserOrReadOnly


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsInProductManagerGroup]
    filterset_class = ProductFilter
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'sku', 'price', 'inventory_quantity', 'updated_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def get_object(self):
        try:
            return super().get_object()
        except:
            return None
    
    @action(detail=True, methods=['post'])
    def update_inventory(self, request, pk=None):
        """
        Update inventory quantity for a product.
        """
        product = self.get_object()
        new_quantity = request.data.get('quantity')

        if new_quantity is None:
            return Response(
                {'error': 'Quantity is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_quantity = int(new_quantity)
            if new_quantity < 0:
                return Response(
                    {'error': 'Quantity cannot be negative'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Create log entry
            log = ProductInventoryLog(
                product=product,
                previous_quantity=product.inventory_quantity,
                new_quantity=new_quantity,
                change_type='manual',
                notes=request.data.get('notes', '')
            )
            
            # Update product quantity
            with transaction.atomic():
                product.inventory_quantity = new_quantity
                product.save()
                log.save()
                
            return Response({'status': 'inventory updated'})
            
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid quantity'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """
        Advanced search endpoint with semantic search using spaCy/sentence-transformers.
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Regular DB search first
        products = self.filter_queryset(
            Product.objects.filter(
                Q(name__icontains=query) | 
                Q(sku__icontains=query) | 
                Q(description__icontains=query)
            )
        )
        
        # If few results, try semantic search
        if products.count() < 10 and len(query) > 3:
            # Try semantic search with sentence-transformers
            all_products = list(Product.objects.all())
            
            # Try to get embeddings from cache first
            query_embedding = self._get_embedding(query)
            
            if query_embedding is not None:
                product_rankings = []
                
                for product in all_products:
                    # Generate a text representation
                    product_text = f"{product.name} {product.sku} {product.description}"
                    product_embedding = self._get_embedding(product_text)
                    
                    if product_embedding is not None:
                        # Calculate similarity
                        similarity = np.dot(query_embedding, product_embedding)
                        product_rankings.append((product, similarity))
                
                # Sort by similarity and add to results
                product_rankings.sort(key=lambda x: x[1], reverse=True)
                
                # Merge semantically found products with DB results
                semantic_products = [p[0] for p in product_rankings[:20]]
                semantic_ids = [p.id for p in semantic_products]
                
                # Add products found semantically that weren't in initial results
                for product in semantic_products:
                    if product not in products:
                        products |= Product.objects.filter(id=product.id)
        
        # Paginate results
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def insights(self, request):
        """
        Get insights about products inventory.
        """
        # Get basic stats
        total_products = Product.objects.count()
        low_stock_count = Product.objects.filter(inventory_quantity__lt=10).count()
        out_of_stock_count = Product.objects.filter(inventory_quantity=0).count()
        avg_price = Product.objects.aggregate(avg_price=Avg('price'))['avg_price'] or 0
        
        # Percentage calculations
        low_stock_percentage = (low_stock_count / total_products * 100) if total_products else 0
        out_of_stock_percentage = (out_of_stock_count / total_products * 100) if total_products else 0
        
        # Detect trending products based on inventory changes
        # Products with most inventory movement in the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        # Get products with most inventory logs
        active_products = Product.objects.annotate(
            log_count=Count('inventory_logs', filter=Q(inventory_logs__timestamp__gte=thirty_days_ago))
        ).filter(log_count__gt=0).order_by('-log_count')[:5]
        
        # Get products with biggest positive inventory changes (restocked items)
        restocked_products = Product.objects.annotate(
            total_increase=Sum(
                'inventory_logs__change',
                filter=Q(
                    inventory_logs__change__gt=0,
                    inventory_logs__timestamp__gte=thirty_days_ago
                )
            )
        ).filter(total_increase__gt=0).order_by('-total_increase')[:5]
        
        # Get products with biggest negative inventory changes (selling fast)
        selling_products = Product.objects.annotate(
            total_decrease=Sum(
                'inventory_logs__change',
                filter=Q(
                    inventory_logs__change__lt=0,
                    inventory_logs__timestamp__gte=thirty_days_ago
                )
            )
        ).filter(total_decrease__lt=0).order_by('total_decrease')[:5]
        
        insights = {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'low_stock_percentage': round(low_stock_percentage, 1),
            'out_of_stock_count': out_of_stock_count,
            'out_of_stock_percentage': round(out_of_stock_percentage, 1),
            'avg_price': round(float(avg_price), 2) if avg_price else 0,
            'trending_products': {
                'most_active': ProductSerializer(active_products, many=True).data,
                'most_restocked': ProductSerializer(restocked_products, many=True).data,
                'selling_fast': ProductSerializer(selling_products, many=True).data,
            }
        }
        
        return Response(insights)
    
    def _get_embedding(self, text):
        """
        Get embedding for text, using cache when possible.
        """
        # Check if AI libraries are available
        if SENTENCE_TRANSFORMER_IMPORT_ERROR and SPACY_IMPORT_ERROR:
            # Log that both embedding options are unavailable
            return None
            
        # Create a cache key from text
        cache_key = f"embedding_{hash(text)}"
        
        # Try to get from cache first
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding
        
        try:
            # Load model if not already loaded
            if not hasattr(self, 'embedding_model'):
                # First try sentence-transformers
                if SentenceTransformer is not None:
                    try:
                        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    except Exception as e:
                        self.embedding_model = None
                
                # Fall back to spaCy if needed
                if self.embedding_model is None and spacy is not None:
                    try:
                        self.embedding_model = spacy.load('en_core_web_md')
                    except:
                        return None
                        
                # If both failed, return None
                if self.embedding_model is None:
                    return None
            
            # Generate embedding based on model type
            if SentenceTransformer is not None and isinstance(self.embedding_model, SentenceTransformer):
                embedding = self.embedding_model.encode(text)
            elif spacy is not None:  # spaCy model
                doc = self.embedding_model(text)
                embedding = doc.vector
            else:
                return None
                
            # Normalize embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
                
            # Cache the embedding
            cache.set(cache_key, embedding, timeout=86400)  # Cache for 24 hours
            
            return embedding
        except Exception as e:
            # In case of errors, return None
            return None


class ProductDiscountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product discounts.
    """
    queryset = ProductDiscount.objects.all()
    serializer_class = ProductDiscountSerializer
    permission_classes = [IsAuthenticated, IsInProductManagerGroup]
    filterset_fields = ['product', 'active']
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_create(self, request):
        """
        Apply a discount to multiple products at once.
        """
        product_ids = request.data.get('product_ids', [])
        discount_data = request.data.get('discount', {})
        
        if not product_ids or not discount_data:
            return Response(
                {'error': 'Product IDs and discount data required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            return Response(
                {'error': 'No valid products found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        created_discounts = []
        
        with transaction.atomic():
            for product in products:
                # Create discount for each product
                discount = ProductDiscount(
                    product=product,
                    name=discount_data.get('name', 'Bulk Discount'),
                    discount_percent=discount_data.get('discount_percent', 0),
                    active=discount_data.get('active', True),
                    start_date=discount_data.get('start_date', timezone.now()),
                    end_date=discount_data.get('end_date')
                )
                discount.save()
                created_discounts.append(discount)
                
        serializer = ProductDiscountSerializer(created_discounts, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShopifyWebhookView(APIView):
    """
    Webhook endpoint for Shopify inventory updates.
    """
    # Skip CSRF and authentication for webhook
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """
        Handle incoming webhook from Shopify for inventory updates.
        """
        # Validate webhook signature - in a real app, you'd validate the Shopify HMAC
        # hmac_header = request.META.get('HTTP_X_SHOPIFY_HMAC_SHA256', '')
        # if not self._verify_webhook(request.body, hmac_header):
        #    return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = WebhookInventoryUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try to find product by Shopify ID first, then by SKU
            shopify_id = serializer.validated_data.get('id')
            sku = serializer.validated_data.get('sku')
            new_quantity = serializer.validated_data.get('inventory_quantity')
            
            product = None
            if shopify_id:
                product = Product.objects.filter(shopify_id=shopify_id).first()
            
            if not product and sku:
                product = Product.objects.filter(sku=sku).first()
            
            if not product:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Create inventory log
            log = ProductInventoryLog(
                product=product,
                previous_quantity=product.inventory_quantity,
                new_quantity=new_quantity,
                change_type='webhook',
                notes=f'Shopify webhook update - {timezone.now().isoformat()}'
            )
            
            # Update product inventory
            with transaction.atomic():
                product.inventory_quantity = new_quantity
                product.save()
                log.save()
                
            return Response({'status': 'success'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _verify_webhook(self, data, hmac_header):
        """
        Verify Shopify webhook signature.
        In a real app, you would implement this with the proper HMAC validation.
        """
        # This is a simplified example, real implementation would be:
        # import hmac, hashlib, base64
        # calculated_hmac = base64.b64encode(
        #     hmac.new(
        #         settings.SHOPIFY_WEBHOOK_SECRET.encode(), 
        #         data, 
        #         hashlib.sha256
        #     ).digest()
        # ).decode()
        # return hmac.compare_digest(calculated_hmac, hmac_header)
        
        # For this exercise, we'll just return True
        return True
