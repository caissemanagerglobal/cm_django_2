from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CmShiftsViewSet, CmOrdersViewSet, CmOrderLineViewSet, CmOrderTypeViewSet, DiscountsViewSet, OrderCancelViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'shifts', CmShiftsViewSet)
router.register(r'orders', CmOrdersViewSet)
router.register(r'order-lines', CmOrderLineViewSet)
router.register(r'order-types', CmOrderTypeViewSet)
router.register(r'discounts', DiscountsViewSet)
router.register(r'order-cancel', OrderCancelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('order/by_table', CmOrdersViewSet.as_view({'get': 'by_table'}), name='by_table'),
    path('order/by_shift', CmOrdersViewSet.as_view({'get': 'by_shift'}), name='by_shift'),
    path('order/by_day', CmOrdersViewSet.as_view({'get': 'by_day'}), name='by_day'),
    path('orderline/suite_ordred', CmOrderLineViewSet.as_view({'get': 'suite_ordred'}), name='suite_ordred'),
    path('order/suite_ordred', CmOrdersViewSet.as_view({'get': 'suite_ordred'}), name='suite_ordred'),
    path('order/by_waiter_and_shift', CmOrdersViewSet.as_view({'get': 'by_waiter_and_shift'}), name='by_waiter_and_shift'),
    path('order/cancel_order_or_line', OrderCancelViewSet.as_view({'post': 'cancel_order_or_line'}), name='cancel_order_or_line'),
    path('order/apply_discount', DiscountsViewSet.as_view({'post': 'apply_discount'}), name='apply_discount'),
    path('order/action_cashdraw', CmOrdersViewSet.as_view({'post': 'action_cashdraw'}), name='action_cashdraw'),

    path('cancel/by_shift', OrderCancelViewSet.as_view({'get': 'by_shift'}), name='by_shift'),
    path('cancel/by_day', OrderCancelViewSet.as_view({'get': 'by_day'}), name='by_day'),

    path('discounts/by_shift', DiscountsViewSet.as_view({'get': 'by_shift'}), name='by_shift'),
    path('discounts/by_day', DiscountsViewSet.as_view({'get': 'by_day'}), name='by_day'),

    path('order/print_ticket', CmOrdersViewSet.as_view({'post': 'print_ticket'}), name='print_ticket')
] 
