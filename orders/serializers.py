from rest_framework import serializers
from .models import CmOrders, CmOrderLine, CmOrderType, Discounts, OrderCancel
from users.serializers import CmEmployeesSerializer, CmClientsSerializer
from pos.serializers import CmShiftsSerializer, CmTableSerializer
from core.serializers import DiscountTypeSerializer

class CmOrderTypeSerializer(serializers.ModelSerializer):
    # parent = serializers.PrimaryKeyRelatedField(queryset=CmOrderType.objects.all(), required=False, allow_null=True)
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        children = CmOrderType.objects.filter(parent=obj)
        return CmOrderTypeSerializer(children, many=True).data

    class Meta:
        model = CmOrderType
        fields = ['id','name','sequence','icon','image','children','select_table','type','select_deliveryboy','in_mobile','select_client','is_archived']

class CmOrderTypeKdsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CmOrderType
        fields = ['id','name','sequence','icon','image','type','select_client','is_archived']


class CmOrderLineSerializer(serializers.ModelSerializer):
    product_variant = serializers.SerializerMethodField()
    uom = serializers.SerializerMethodField()
    cm_order_type = CmOrderTypeSerializer()
    combo_prods = serializers.SerializerMethodField()
    combo_supps = serializers.SerializerMethodField()

    class Meta:
        model = CmOrderLine
        fields = '__all__'

    def get_product_variant(self, obj):
        from products.serializers import ProductVariantSerializer
        return ProductVariantSerializer(obj.product_variant).data

    def get_uom(self, obj):
        from products.serializers import UomSerializer
        return UomSerializer(obj.uom).data

    def get_cm_order_type(self, obj):
        return CmOrderTypeSerializer(obj.cm_order_type).data

    def get_combo_prods(self, obj):
        from products.serializers import ProductVariantSerializer
        return ProductVariantSerializer(obj.combo_prods.all(), many=True).data

    def get_combo_supps(self, obj):
        from products.serializers import ProductVariantSerializer
        return ProductVariantSerializer(obj.combo_supps.all(), many=True).data

class CmOrdersSerializer(serializers.ModelSerializer):
    cm_waiter = CmEmployeesSerializer(read_only=True)
    cm_shift = CmShiftsSerializer(read_only=True)
    cm_table = CmTableSerializer(read_only=True)
    delivery_guy = CmEmployeesSerializer(read_only=True)
    client = CmClientsSerializer(read_only=True)
    cm_order_type = CmOrderTypeSerializer()


    created_by = CmEmployeesSerializer(read_only=True)
    updated_by = CmEmployeesSerializer(read_only=True)
    order_lines = CmOrderLineSerializer(many=True)
    paid_amount = serializers.ReadOnlyField(source='paidAmount')

    class Meta:
        model = CmOrders
        fields = '__all__'

    def create(self, validated_data):
        orderlines_data = validated_data.pop('order_lines')
        order = CmOrders.objects.create(**validated_data)
        for orderline_data in orderlines_data:
            CmOrderLine.objects.create(order=order, **orderline_data)
        return order

    def update(self, instance, validated_data):
        orderlines_data = validated_data.pop('order_lines')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for orderline_data in orderlines_data:
            orderline_id = orderline_data.get('id', None)
            if orderline_id:
                orderline = CmOrderLine.objects.get(id=orderline_id, order=instance)
                for attr, value in orderline_data.items():
                    if attr != 'id':
                        setattr(orderline, attr, value)
                orderline.save()
            else:
                CmOrderLine.objects.create(order=instance, **orderline_data)

        return instance
class DiscountsSerializer(serializers.ModelSerializer):
    discount_type = DiscountTypeSerializer()
    order = serializers.SerializerMethodField()
    orderline = serializers.SerializerMethodField()

    class Meta:
        model = Discounts
        fields = '__all__'

    def get_order(self, obj):
        return CmOrdersSerializer(obj.order).data

    def get_orderline(self, obj):
        return CmOrderLineSerializer(obj.orderline).data
    
class OrderCancelSerializer(serializers.ModelSerializer):
    created_by = CmEmployeesSerializer()
    order = CmOrdersSerializer()
    orderline = CmOrderLineSerializer()

    class Meta:
        model = OrderCancel
        fields = '__all__'

