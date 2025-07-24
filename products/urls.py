from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'discounts', views.ProductDiscountViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/shopify/inventory/', views.ShopifyWebhookView.as_view(), name='shopify-webhook'),
] 