from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteSettingsViewSet, ConfigSettingsViewSet, TaxViewSet, DiscountTypeViewSet, DefinedNotesViewSet, HealthCheckViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'site-settings', SiteSettingsViewSet, basename='site-settings')
router.register(r'config-settings', ConfigSettingsViewSet)
router.register(r'taxes', TaxViewSet)
router.register(r'discount-type', DiscountTypeViewSet)
router.register(r'notes', DefinedNotesViewSet) 
urlpatterns = [
    path('', include(router.urls)),
    path('check', HealthCheckViewSet.as_view({'get': 'check'}), name='check'),
]
