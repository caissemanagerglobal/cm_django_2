from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework_api_key.permissions import HasAPIKey
from .models import SiteSettings, ConfigSettings, Tax, DiscountType, DefinedNotes
from .serializers import SiteSettingsSerializer, ConfigSettingsSerializer, TaxSerializer, DiscountTypeSerializer, DefinedNotesSerializer, SiteSettingsWriteSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@permission_classes([HasAPIKey])
class HealthCheckViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def check(self, request):
        # Basic health check response
        return Response({"status": "OK"}, status=status.HTTP_200_OK)

@permission_classes([IsAuthenticated])
class SiteSettingsViewSet(viewsets.ModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer


    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SiteSettingsWriteSerializer
        return SiteSettingsSerializer


@permission_classes([IsAuthenticated])
class ConfigSettingsViewSet(viewsets.ModelViewSet):
    queryset = ConfigSettings.objects.all()
    serializer_class = ConfigSettingsSerializer

@permission_classes([IsAuthenticated])
class TaxViewSet(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer

@permission_classes([IsAuthenticated])
class DiscountTypeViewSet(viewsets.ModelViewSet):
    queryset = DiscountType.objects.all()
    serializer_class = DiscountTypeSerializer

@permission_classes([IsAuthenticated])
class DefinedNotesViewSet(viewsets.ModelViewSet):
    queryset = DefinedNotes.objects.all()
    serializer_class = DefinedNotesSerializer
