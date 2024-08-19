# your_app_name/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CmEmployeesViewSet, CmClientsViewSet, CmRoleViewSet, CmFeatureViewSet, ValidateEmployee, ValidateBadgeNumber, ValidateEmployeeBackoffice

router = DefaultRouter(trailing_slash=False)
router.register(r'employees', CmEmployeesViewSet)
router.register(r'roles', CmRoleViewSet)
router.register(r'features', CmFeatureViewSet)
router.register(r'clients', CmClientsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('employee/validate', ValidateEmployee.as_view(), name='validate_employee'),
    path('employees/filter_by_type', CmEmployeesViewSet.as_view({'get': 'filter_by_type'}), name='filter_by_type'),
    path('employee/validate_badge', ValidateBadgeNumber.as_view(), name='validate_badge_number'),
    path('employee/validate_backoffice', ValidateEmployeeBackoffice.as_view(), name='validate_backoffice'),
]
