from rest_framework import serializers
from .models import CmDays, CmPos, CmTable, CmShifts, CmFloor
from payments.models import CmClosingBalances
from users.serializers import CmEmployeesSerializer
from django.utils.module_loading import import_string

class CmDaysSerializer(serializers.ModelSerializer):
    opening_employee = CmEmployeesSerializer()
    closing_employee = CmEmployeesSerializer()
    revenue_system = serializers.SerializerMethodField()
    revenue_declared = serializers.SerializerMethodField()

    class Meta:
        model = CmDays
        fields = '__all__'

    def get_revenue_system(self, obj):
        return obj.revenueSystem

    def get_revenue_declared(self, obj):
        return obj.revenueDeclared
        

class CmFloorSerializer(serializers.ModelSerializer):
    tables = serializers.SerializerMethodField()

    class Meta:
        model = CmFloor
        fields = '__all__'
        

    def get_tables(self, obj):
        tables = CmTable.objects.filter(floor=obj)
        return CmTableSerializer(tables, many=True).data

class CmTableSerializer(serializers.ModelSerializer):
    # floor = CmFloorSerializer()
    class Meta:
        model = CmTable
        fields = '__all__'
        
        
class CmPosSerializer(serializers.ModelSerializer):
    open_shift = serializers.SerializerMethodField()

    class Meta:
        model = CmPos
        fields = '__all__'
        

    def get_open_shift(self, obj):
        try:
            open_shift = CmShifts.objects.get(cm_pos=obj, status__in=["Open", "opening_control"])
            return CmShiftsSerializer(open_shift).data
        except CmShifts.DoesNotExist:
            return None

class CmShiftsSerializer(serializers.ModelSerializer):
    cm_employee = CmEmployeesSerializer()
    closing_balances = serializers.SerializerMethodField()

    class Meta:
        model = CmShifts
        fields = '__all__'

    def get_closing_balances(self, obj):
        CmClosingBalancesSerializer = import_string('payments.serializers.CmClosingBalancesSerializer')
        closing_balances = CmClosingBalances.objects.filter(cm_shift=obj)
        return CmClosingBalancesSerializer(closing_balances, many=True).data
        

