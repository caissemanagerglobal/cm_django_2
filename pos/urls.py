from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CmDaysViewSet, CmPosViewSet, CmTableViewSet, CmShiftsViewSet, CmFloorViewSet, GeneralDataViewSet, GeneralDataKdsViewSet,PasswordCheckViewSet, DashboardMetricsAPIView, DashboardMetricsDayAPIView

router = DefaultRouter(trailing_slash=False)
router.register(r'days', CmDaysViewSet)
router.register(r'pos', CmPosViewSet)
router.register(r'tables', CmTableViewSet)
router.register(r'shifts', CmShiftsViewSet)
router.register(r'floors', CmFloorViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('days/check_open_days', CmDaysViewSet.as_view({'get': 'check_open_days'}), name='check_open_days'),
    path('general-data', GeneralDataViewSet.as_view(), name='general_data'),
    path('general-data-kds', GeneralDataKdsViewSet.as_view(), name='general_data'),
    path('days/close_day', CmDaysViewSet.as_view({'post': 'close_day'}), name='close_day'),
    path('shifts/update_shift', CmShiftsViewSet.as_view({'post': 'update_shift'}), name='update_shift'),
    path('shifts/close_shift', CmDaysViewSet.as_view({'post': 'close_shift'}), name='close_shift'),
    path('shifts/by_day', CmDaysViewSet.as_view({'get': 'by_day'}), name='by_day'),
    path('dashboard-metrics', DashboardMetricsAPIView.as_view(), name='dashboard_metrics'),
    path('dashboard-metrics-day', DashboardMetricsDayAPIView.as_view(), name='dashboard_metrics_day'),

    path('admin', PasswordCheckViewSet.as_view({'post': 'check_password'}), name='check_password'),
]
