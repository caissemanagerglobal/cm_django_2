from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CmClosingBalancesViewSet, CmClientDebtsViewSet, CmPaymentsViewSet, CmDropsViewSet, CmPaymentMethodsViewSet, CmPaymentMethodsAttributesViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'closing-balances', CmClosingBalancesViewSet)
router.register(r'client-debts', CmClientDebtsViewSet)
router.register(r'payments', CmPaymentsViewSet)
router.register(r'drops', CmDropsViewSet)
router.register(r'payment-methods', CmPaymentMethodsViewSet)
router.register(r'payment-method-attributes', CmPaymentMethodsAttributesViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('by_shift', CmPaymentsViewSet.as_view({'get': 'by_shift'}), name='by_shift'),
    path('by_payment_method', CmPaymentsViewSet.as_view({'get': 'by_payment_method'}), name='by_payment_method'),
    path('by_order', CmPaymentsViewSet.as_view({'get': 'by_order'}), name='by_order'),
    path('by_day', CmPaymentsViewSet.as_view({'get': 'by_day'}), name='by_day'),
    path('drops/by_shift', CmDropsViewSet.as_view({'get': 'by_shift'}), name='by_shift'),
    path('drops/by_day', CmDropsViewSet.as_view({'get': 'by_day'}), name='by_day'),
]
