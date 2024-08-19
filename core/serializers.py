from rest_framework import serializers
from .models import SiteSettings, ConfigSettings, Tax, DiscountType, DefinedNotes
from users.models import CmEmployees
from users.serializers import CmEmployeesSerializer

class SiteSettingsWriteSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=CmEmployees.objects.all())
    updated_by = serializers.PrimaryKeyRelatedField(queryset=CmEmployees.objects.all())

    class Meta:
        model = SiteSettings
        fields = '__all__'

    def create(self, validated_data):
        return SiteSettings.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SiteSettingsSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(queryset=CmEmployees.objects.all())
    updated_by = serializers.PrimaryKeyRelatedField(queryset=CmEmployees.objects.all())

    class Meta:
        model = SiteSettings
        fields = '__all__'

class ConfigSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConfigSettings
        fields = '__all__'

class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = '__all__'

class DiscountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountType
        fields = '__all__'


class DefinedNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefinedNotes
        fields = '__all__'
