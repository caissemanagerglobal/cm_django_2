from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CmPreparationDisplayStageViewSet, CmPreparationDisplayViewSet, CmKdsOrderViewSet, CmKdsOrderlineViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'kds-stages', CmPreparationDisplayStageViewSet)
router.register(r'preparation-displays', CmPreparationDisplayViewSet)
router.register(r'kds-orders', CmKdsOrderViewSet)
router.register(r'kds-orderlines', CmKdsOrderlineViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('display_orders', CmPreparationDisplayViewSet.as_view({'get': 'display_orders'}), name='display_orders'),
    path('change_stage', CmKdsOrderViewSet.as_view({'get': 'change_stage'}), name='change_stage'),
    path('display_orders_by_stage', CmPreparationDisplayViewSet.as_view({'get': 'display_orders_by_stage'}), name='display_orders_by_stage'),
    path('toggle_is_done', CmKdsOrderlineViewSet.as_view({'get': 'toggle_is_done'}), name='toggle_is_done'),
    path('clear', CmKdsOrderViewSet.as_view({'get': 'clear'}), name='clear'),
    path('get_categories_and_products', CmPreparationDisplayViewSet.as_view({'get': 'get_categories_and_products'}), name='get_categories_and_products'),
]
