from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, UomViewSet, ProductVariantViewSet, ProductStepViewSet, ProductQuantityViewSet, KitchenPosteViewSet, ProductVariantAttributeSet, ProductVariantAttributeValueSet

router = DefaultRouter(trailing_slash=False)
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'uom', UomViewSet)
router.register(r'variant-attribute', ProductVariantAttributeSet)
router.register(r'variant-attribute-value', ProductVariantAttributeValueSet)
router.register(r'product-variants', ProductVariantViewSet)
router.register(r'product-steps', ProductStepViewSet)
router.register(r'product-quantity', ProductQuantityViewSet)
router.register(r'kitchen-poste', KitchenPosteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('product-quantity/by-variant', ProductQuantityViewSet.as_view({'get': 'by_variant'}), name='product-quantity-by-variant'),
    path('product-steps/by-variant', ProductStepViewSet.as_view({'get': 'by_variant'}), name='product-step-by-variant'),
    path('product/override_availability', ProductVariantViewSet.as_view({'post': 'override_availability'}), name='override_availability'),

]
