from rest_framework import serializers
from .models import CmPreparationDisplay, CmPreparationDisplayStage, CmKdsOrder, CmKdsOrderline

class CmPreparationDisplayStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CmPreparationDisplayStage
        fields = '__all__'

class CmPreparationDisplaySerializer(serializers.ModelSerializer):
    stage_ids = serializers.PrimaryKeyRelatedField(queryset=CmPreparationDisplayStage.objects.all(), many=True)

    class Meta:
        model = CmPreparationDisplay
        fields = '__all__'

class CmKdsOrderSerializer(serializers.ModelSerializer):
    cm_pos_order = serializers.SerializerMethodField()
    orderlines = serializers.SerializerMethodField()

    class Meta:
        model = CmKdsOrder
        fields = '__all__'

    def get_cm_pos_order(self, obj):
        from orders.serializers import CmOrdersSerializer
        return CmOrdersSerializer(obj.cm_pos_order).data
    
    def get_orderlines(self, obj):
        orderlines = CmKdsOrderline.objects.filter(cm_kds_order=obj)
        return CmKdsOrderlineSerializer(orderlines, many=True).data

class CmKdsOrderlineSerializer(serializers.ModelSerializer):
    cm_pos_orderline = serializers.SerializerMethodField()

    class Meta:
        model = CmKdsOrderline
        fields = '__all__'

    def get_cm_pos_orderline(self, obj):
        from orders.serializers import CmOrderLineSerializer
        return CmOrderLineSerializer(obj.cm_pos_orderline).data
