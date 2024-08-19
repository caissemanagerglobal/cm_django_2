from rest_framework import serializers
from .models import CmClosingBalances, CmPaymentsAttribute, CmPaymentMethodsAttributes, CmClientDebts, CmPayments, CmDrops, CmPaymentMethods
from pos.serializers import CmShiftsSerializer
from users.serializers import CmClientsSerializer, CmEmployeesSerializer
from orders.models import CmOrders
import threading

class CmPaymentMethodsAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmPaymentMethodsAttributes
        fields = '__all__'

class CmPaymentMethodsSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=CmPaymentMethods.objects.all(), required=False, allow_null=True)
    payment_method_attributte = CmPaymentMethodsAttributesSerializer(many=True, required=False)  # Make optional

    class Meta:
        model = CmPaymentMethods
        fields = '__all__'

    def create(self, validated_data):
        attributes_data = validated_data.pop('payment_method_attributte', [])
        payment_method = CmPaymentMethods.objects.create(**validated_data)
        for attribute_data in attributes_data:
            CmPaymentMethodsAttributes.objects.create(payment_method=payment_method, **attribute_data)
        return payment_method

    def update(self, instance, validated_data):
        attributes_data = validated_data.pop('payment_method_attributte', None)
        if attributes_data is not None:
            instance.payment_method_attributte.all().delete()
            for attribute_data in attributes_data:
                CmPaymentMethodsAttributes.objects.create(payment_method=instance, **attribute_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class CmClosingBalancesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmClosingBalances
        fields = '__all__'

class CmPaymentsAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmPaymentsAttribute
        fields = ['cm_shift','system_amount','cashier_amount','verification_amount','verification_employee','is_archived']

class CmPaymentsSerializer(serializers.ModelSerializer):
    cm_order = serializers.PrimaryKeyRelatedField(queryset=CmOrders.objects.all())
    cm_payment_method = serializers.PrimaryKeyRelatedField(queryset=CmPaymentMethods.objects.all())
    payment_attribute = CmPaymentsAttributeSerializer(many=True)

    class Meta:
        model = CmPayments
        fields = '__all__'

class CmClientDebtsSerializer(serializers.ModelSerializer):
    cm_payment_method = CmPaymentMethodsSerializer()
    cm_payment = CmPaymentsSerializer()
    class Meta:
        model = CmClientDebts
        fields = '__all__'

class CmDropsSerializer(serializers.ModelSerializer):
    cm_employee = CmEmployeesSerializer()
    cm_shift = CmShiftsSerializer()

    class Meta:
        model = CmDrops
        fields = '__all__'
