import uuid
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from datetime import datetime

class CmOrderType(models.Model):
    TYPE_CHOICES = [
        ('delivery', 'Delivery'),
        ('onPlace', 'On Place'),
        ('takeAway', 'Take Away'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    sequence = models.IntegerField()
    select_table = models.BooleanField(default=True)
    select_deliveryboy = models.BooleanField(default=False)
    select_client = models.BooleanField(default=False)
    in_mobile = models.BooleanField(default=False)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='onPlace',
    )
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.DO_NOTHING)
    icon = models.BinaryField(null=True)
    image = models.BinaryField(null=True)
    is_archived = models.BooleanField(default=False)

class CmOrders(models.Model):
    id = models.AutoField(primary_key=True)
    ref = models.CharField(max_length=255, null=True)
    cm_waiter = models.ForeignKey('users.CmEmployees', related_name='orders', on_delete=models.DO_NOTHING, null=True)
    cm_shift = models.ForeignKey('pos.CmShifts', related_name='order_shift', on_delete=models.DO_NOTHING)
    cm_table = models.ForeignKey('pos.CmTable', related_name='order_table', null=True, on_delete=models.DO_NOTHING)
    delivery_guy = models.ForeignKey('users.CmEmployees', related_name='delivery_guy', null=True, on_delete=models.DO_NOTHING)
    discount_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    client = models.ForeignKey('users.CmClients', on_delete=models.DO_NOTHING, null=True)
    notes = models.CharField(null=True, max_length=255)
    customer_count = models.IntegerField()
    one_time = models.BooleanField()
    status = models.CharField(max_length=255)
    cm_order_type = models.ForeignKey(CmOrderType, related_name='orders', on_delete=models.DO_NOTHING)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.CmEmployees', related_name='created_orders', on_delete=models.DO_NOTHING)
    updated_by = models.ForeignKey('users.CmEmployees', related_name='updated_orders', on_delete=models.DO_NOTHING)
    is_archived = models.BooleanField(default=False)

    


    @property
    def paidAmount(self):
        # Sum the amount of all related payments
        return self.payments.aggregate(total_paid=models.Sum('amount'))['total_paid'] or 0.0


    def generate_ref(self):
        shift_orders_count = CmOrders.objects.filter(cm_shift=self.cm_shift).count()
        global_orders_count = CmOrders.objects.count()
        return f"{self.cm_shift.id}-{shift_orders_count + 1}-{global_orders_count + 1}"

@receiver(post_save, sender=CmOrders)
def set_order_ref(sender, instance, created, **kwargs):
    if created and not instance.ref:
        instance.ref = instance.generate_ref()
        instance.save()

class CmOrderLine(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(CmOrders, related_name='order_lines', on_delete=models.DO_NOTHING, null=True)  # Add related_name
    price = models.FloatField(default=0.0)
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.DO_NOTHING)
    uom = models.ForeignKey('products.Uom', on_delete=models.DO_NOTHING)
    discount_amount = models.FloatField(default=0.0, null=True)
    customer_index = models.IntegerField()
    notes = models.TextField()
    qty = models.FloatField()
    cancelled_qty = models.FloatField(default=0.0)
    suite_commande = models.BooleanField(default=False)
    cm_order_type = models.ForeignKey(CmOrderType, related_name='order_lines', on_delete=models.DO_NOTHING)
    suite_ordred = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_ordred = models.BooleanField(default=False)
    combo_prods = models.ManyToManyField('products.ProductVariant', related_name='combo_prods')
    combo_supps = models.ManyToManyField('products.ProductVariant', related_name='combo_supps')
    is_archived = models.BooleanField(default=False)

class Discounts(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(null=True, max_length=255)
    discount_type = models.ForeignKey('core.DiscountType', related_name="discount_discount_type", null=True, on_delete=models.DO_NOTHING)
    order = models.ForeignKey(CmOrders, related_name="discounts", null=True, on_delete=models.DO_NOTHING)
    orderline = models.ForeignKey(CmOrderLine, related_name="discounts", null=True, on_delete=models.DO_NOTHING)
    amount = models.FloatField(default=0.0)
    is_archived = models.BooleanField(default=False)

class OrderCancel(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(CmOrders, related_name="cancellations", null=True, on_delete=models.DO_NOTHING)
    orderline = models.ForeignKey(CmOrderLine, related_name="cancellations", null=True, on_delete=models.DO_NOTHING)
    quantity = models.FloatField(default=0.0)
    created_by = models.ForeignKey('users.CmEmployees', on_delete=models.DO_NOTHING)
    reason = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)
