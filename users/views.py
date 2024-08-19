# views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CmEmployees, CmRole, CmFeature, CmClients
from .serializers import CmEmployeesSerializer, CmClientsSerializer, CmRoleSerializer, CmFeatureSerializer, CmEmployeesWriteSerializer, CmRoleWriteSerializer, CmClientsWriteSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmployeeTokenObtainPairSerializer
from kds.serializers import CmPreparationDisplaySerializer

class EmployeeTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmployeeTokenObtainPairSerializer


@permission_classes([HasAPIKey])
class CmEmployeesViewSet(viewsets.ModelViewSet):
    queryset = CmEmployees.objects.all()
    permission_classes = [HasAPIKey]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CmEmployeesWriteSerializer
        return CmEmployeesSerializer


    @action(detail=False, methods=['get'])
    def filter_by_type(self, request):
        employee_type = request.query_params.get('employee_type', None)
        if employee_type is not None:
            employees = self.queryset.filter(position=employee_type, has_pos=True)
            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        return Response({"error": "employee_type parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([HasAPIKey])
class ValidateEmployee(APIView):
    def post(self, request, *args, **kwargs):
        employee_id = request.data.get('employee')
        pin_code = request.data.get('pin_code')

        if not employee_id or not pin_code:
            return Response({"error": "Both employee and pin_code are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = CmEmployees.objects.get(id=employee_id)
            if check_password(pin_code, employee.pin_code):
                token_data = EmployeeTokenObtainPairSerializer.get_token(employee)
                return Response({
                    'message': 'Employee validated successfully',
                    'refresh': str(token_data),
                    'access': str(token_data.access_token),
                    'employee': {
                        'id': employee.id,
                        'name': employee.name,
                        'position': employee.position,
                        'preparation_display': CmPreparationDisplaySerializer(employee.preparation_display).data
                    }
                })
            else:
                return Response({"error": "Invalid employee or pin_code"}, status=status.HTTP_404_NOT_FOUND)
        except CmEmployees.DoesNotExist:
            return Response({"error": "Invalid employee or pin_code"}, status=status.HTTP_404_NOT_FOUND)

@permission_classes([HasAPIKey])
class ValidateBadgeNumber(APIView):
    def post(self, request, *args, **kwargs):
        badge_number = request.data.get('badge_number')
        
        if not badge_number:
            return Response({"error": "Badge number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = CmEmployees.objects.get(badge_number=badge_number)
            serializer = CmEmployeesSerializer(employee)
            token_data = EmployeeTokenObtainPairSerializer.get_token(employee)
            return Response({
                'employee': serializer.data,
                'refresh': str(token_data),
                'access': str(token_data.access_token),
            })
        except CmEmployees.DoesNotExist:
            return Response({"error": "Invalid badge number"}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([HasAPIKey])
class ValidateEmployeeBackoffice(APIView):
    def post(self, request, *args, **kwargs):
        employee_id = request.data.get('employee')
        if not employee_id:
            return Response({"error": "employee is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = CmEmployees.objects.get(id=employee_id)
            serializer = CmEmployeesSerializer(employee)
            token_data = EmployeeTokenObtainPairSerializer.get_token(employee)
            return Response({
                'employee': serializer.data,
                'refresh': str(token_data),
                'access': str(token_data.access_token),
            })
        except CmEmployees.DoesNotExist:
            return Response({"error": "Invalid badge number"}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([HasAPIKey])
class CmRoleViewSet(viewsets.ModelViewSet):
    queryset = CmRole.objects.all()
    permission_classes = [HasAPIKey]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CmRoleWriteSerializer
        return CmRoleSerializer

@permission_classes([HasAPIKey])
class CmFeatureViewSet(viewsets.ModelViewSet):
    queryset = CmFeature.objects.all()
    serializer_class = CmFeatureSerializer

@permission_classes([IsAuthenticated])
class CmClientsViewSet(viewsets.ModelViewSet):
    queryset = CmClients.objects.all()
    permission_classes = [IsAuthenticated]  # Adjust permission classes as needed

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CmClientsWriteSerializer
        return CmClientsSerializer
