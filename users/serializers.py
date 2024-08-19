from rest_framework import serializers
from .models import CmEmployees, CmRole, CmFeature, CmClients
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sessions.models import Session
from django.utils import timezone
import logging

logger = logging.getLogger('django')


class CmFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmFeature
        fields = '__all__'

class CmRoleSerializer(serializers.ModelSerializer):
    cm_features = CmFeatureSerializer(many=True)

    class Meta:
        model = CmRole
        fields = '__all__'

class CmRoleWriteSerializer(serializers.ModelSerializer):
    cm_features = serializers.PrimaryKeyRelatedField(queryset=CmFeature.objects.all(), many=True, required=False)

    class Meta:
        model = CmRole
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True},
            'cm_features': {'required': False},
        }

    def create(self, validated_data):
        features = validated_data.pop('cm_features', [])
        role = CmRole.objects.create(**validated_data)
        role.cm_features.set(features)
        return role

    def update(self, instance, validated_data):
        features = validated_data.pop('cm_features', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if features is not None:
            instance.cm_features.set(features)

        return instance

class CmEmployeesWriteSerializer(serializers.ModelSerializer):
    cm_role = serializers.PrimaryKeyRelatedField(queryset=CmRole.objects.all())

    class Meta:
        model = CmEmployees
        fields = '__all__'

    def create(self, validated_data):
        print("Validated data:", validated_data)  # Debugging line
        cm_role = validated_data.pop('cm_role')
        employee = CmEmployees.objects.create(cm_role=cm_role, **validated_data)
        return employee

    def update(self, instance, validated_data):
        cm_role = validated_data.pop('cm_role', None)
        if cm_role is not None:
            instance.cm_role = cm_role
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class CmEmployeesSerializer(serializers.ModelSerializer):
    cm_role = CmRoleSerializer()

    class Meta:
        model = CmEmployees
        fields = ["id","name", "position", "cm_role","preparation_display",'is_archived']



class CmClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmClients
        fields = '__all__'

class CmClientsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmClients
        fields = '__all__'


class EmployeeTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, employee):
        token = RefreshToken.for_user(employee)

        employee.last_login_time = timezone.now()
        employee.save(update_fields=['last_login_time'])

        token['employee_id'] = employee.id
        token['name'] = employee.name
        token['position'] = employee.position
        token['last_login_time'] = employee.last_login_time.timestamp()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        data['employee'] = {
            'id': self.user.id,
            'name': self.user.name,
            'position': self.user.position,
        }

        return data