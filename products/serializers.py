from rest_framework import serializers
from kds.models import CmPreparationDisplay
from .models import Product, Category, Uom, ProductVariant, ProductStep, ProductQuantity, KitchenPoste, ProductVariantAttribute, ProductVariantAttributeValue
from kds.serializers import CmPreparationDisplaySerializer
from core.serializers import TaxSerializer
from core.models import Tax

class ProductQuantitySerializer(serializers.ModelSerializer):
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = ProductQuantity
        fields = ['product_variant', 'quantity']

class ProductQuantityCreateSerializer(serializers.ModelSerializer):
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = ProductQuantity
        fields = ['product_variant', 'quantity']

    def validate(self, attrs):
        product_variant = attrs.get('product_variant')
        if ProductQuantity.objects.filter(product_variant=product_variant).exists():
            raise serializers.ValidationError({"product_variant": "This product variant already has a quantity entry."})
        return attrs

class ProductQuantityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductQuantity
        fields = ['quantity']

class UomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Uom
        fields = '__all__'

class ProductVariantAttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantAttributeValue
        fields = '__all__'

class ProductVariantAttributeSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    def get_attributes(self, obj):
        attributes = ProductVariantAttributeValue.objects.filter(variant_attribute=obj)
        return ProductVariantAttributeValueSerializer(attributes, many=True).data

    class Meta:
        model = ProductVariantAttribute
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'description', 'image', 'is_active', 'variants']

    def get_variants(self, obj):
        variants = ProductVariant.objects.filter(product=obj, is_active=True)
        return ProductVariantSerializer(variants, many=True).data

class ProductWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'description', 'image', 'is_active']
        extra_kwargs = {
            'name': {'required': False},
            'category': {'required': False},
            'description': {'required': False},
            'image': {'required': False},
            'is_active': {'required': False},
        }

    def create(self, validated_data):
        return Product.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ProductVariantSerializer(serializers.ModelSerializer):
    # product = ProductSerializer(read_only=True)
    tax = TaxSerializer(read_only=True)
    cm_uom = UomSerializer(read_only=True)
    variant_attributes = ProductVariantAttributeSerializer(many=True, read_only=True)
    steps = serializers.SerializerMethodField()

    def get_steps(self, obj):
        steps = ProductStep.objects.filter(product_variant=obj)
        return ProductStepPosSerializer(steps, many=True).data

    class Meta:
        model = ProductVariant
        fields = '__all__'

class ProductVariantWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=True)
    tax = serializers.PrimaryKeyRelatedField(queryset=Tax.objects.all(), required=True)
    cm_uom = serializers.PrimaryKeyRelatedField(queryset=Uom.objects.all(), required=True)
    variant_attributes = serializers.PrimaryKeyRelatedField(queryset=ProductVariantAttribute.objects.all(), many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True},
            'price_ttc': {'required': True},
            'description': {'required': False},
            'image': {'required': False},
            'is_active': {'required': False},
            'in_mobile_pos': {'required': False},
            'in_pos': {'required': False},
            'is_available': {'required': False},
            'barcode': {'required': False},
            'reference': {'required': False},
            'is_menu': {'required': False},
            'is_quantity_check': {'required': False},
            'variant_attributes': {'required': False}
        }

    def create(self, validated_data):
        print(validated_data)
        variant_attributes = validated_data.pop('variant_attributes', [])
        product_variant = ProductVariant.objects.create(**validated_data)
        product_variant.variant_attributes.set(variant_attributes)
        return product_variant

    def update(self, instance, validated_data):
        variant_attributes = validated_data.pop('variant_attributes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if variant_attributes is not None:
            instance.variant_attributes.set(variant_attributes)

        return instance

class CategorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    is_parent = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id','is_parent', 'name', 'is_displayed', 'products', 'children', 'sequence','image','is_archived']

    def get_products(self, obj):
        products = Product.objects.filter(category=obj)
        return ProductSerializer(products, many=True).data

    def get_children(self, obj):
        children = Category.objects.filter(parent=obj, is_displayed=True)
        return CategorySerializer(children, many=True).data

    
    def get_is_parent(self, obj):
        return obj.parent is None

class CategoryGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
    

class CategoryWriteSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)  # Add image field

    class Meta:
        model = Category
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': False},
            'is_displayed': {'required': False},
            'parent': {'required': False},
        }

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        category = Category.objects.create(**validated_data)
        if image:
            category.image = image
            category.save()
        return category

    def update(self, instance, validated_data):
        image = validated_data.pop('image', None)
        instance = super().update(instance, validated_data)
        if image:
            instance.image = image
            instance.save()
        return instance

class SimpleProductVariantSerializer(serializers.ModelSerializer):
    """A simplified serializer for ProductVariant to avoid recursion"""
    class Meta:
        model = ProductVariant
        fields = ['id', 'name','is_archived']

class ProductStepSerializer(serializers.ModelSerializer):
    product_variants = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), many=True)
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = ProductStep
        fields = '__all__'


class ProductStepPosSerializer(serializers.ModelSerializer):
    product_variants = ProductVariantSerializer(many=True)
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = ProductStep
        fields = '__all__'

class KitchenPosteSerializer(serializers.ModelSerializer):
    product_variants = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), many=True, required=False  # Optional field
    )
    screen_poste = serializers.PrimaryKeyRelatedField(
        queryset=CmPreparationDisplay.objects.all()  # Accept a single PK value
    )

    class Meta:
        model = KitchenPoste
        fields = '__all__'

    def create(self, validated_data):
        product_variants = validated_data.pop('product_variants', [])
        kitchen_poste = KitchenPoste.objects.create(**validated_data)
        kitchen_poste.product_variants.set(product_variants)  # Set the many-to-many field
        return kitchen_poste

    def update(self, instance, validated_data):
        product_variants = validated_data.pop('product_variants', [])
        instance = super().update(instance, validated_data)
        instance.product_variants.set(product_variants)
        return instance
