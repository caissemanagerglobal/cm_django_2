# products/models.py
from django.db import models
from core.models import Tax
from kds.models import CmPreparationDisplay

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    sequence = models.IntegerField(default=1)
    is_displayed = models.BooleanField(default=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Uom(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

class ProductVariantAttribute(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

class ProductVariantAttributeValue(models.Model):
    id = models.AutoField(primary_key=True)
    variant_attribute = models.ForeignKey(ProductVariantAttribute, null=True, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    extra_price = models.FloatField(default=0.0)
    is_archived = models.BooleanField(default=False)

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='category', on_delete=models.DO_NOTHING)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/')
    is_active = models.BooleanField()
    is_archived = models.BooleanField(default=False)


class ProductVariant(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    price_ttc = models.FloatField()
    tax = models.ForeignKey(Tax, on_delete=models.DO_NOTHING)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/', null=True)
    is_active = models.BooleanField(default=True)
    in_mobile_pos = models.BooleanField(default=True)
    in_pos = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    barcode = models.CharField()
    is_archived = models.BooleanField(default=False)
    
    reference = models.CharField(max_length=255)
    is_menu = models.BooleanField()
    cm_uom = models.ForeignKey(Uom, on_delete=models.DO_NOTHING)
    is_quantity_check = models.BooleanField(default=False)
    variant_attributes = models.ManyToManyField(ProductVariantAttributeValue)


class ProductQuantity(models.Model):
    id = models.AutoField(primary_key=True)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING)
    quantity = models.FloatField(default=0.0)
    is_archived = models.BooleanField(default=False)

class ProductStep(models.Model):
    id = models.AutoField(primary_key=True)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=255)
    is_required = models.BooleanField()
    is_supplement = models.BooleanField()
    number_of_products = models.IntegerField()
    product_variants = models.ManyToManyField(ProductVariant,related_name='menu_options')
    is_archived = models.BooleanField(default=False)

class KitchenPoste(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    product_variants = models.ManyToManyField(ProductVariant, related_name='kitchen_products')
    by_ip = models.BooleanField(default=False)
    screen = models.BooleanField(default=False)
    printer_ip = models.CharField(max_length=255, null=True)
    screen_poste = models.ForeignKey(CmPreparationDisplay, related_name='kitchen_poste_screen', on_delete=models.DO_NOTHING)
    is_archived = models.BooleanField(default=False)