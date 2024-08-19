from django.db import models
from orders.models import CmOrders, CmOrderLine
from uuid import uuid4

class CmPreparationDisplayStage(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(null=True,max_length=255)
    is_to_preparate = models.BooleanField(null=True)
    is_done = models.BooleanField(null=True)
    color = models.CharField(null=True)
    sequence = models.IntegerField(null=True)
    is_archived = models.BooleanField(default=False)

    @property
    def OrderCount(self):
        return "Total Orders in Stage"

class CmPreparationDisplay(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(null=True,max_length=255)
    is_pilotage = models.BooleanField(null=True)
    average_time = models.IntegerField(null=True)
    stage_ids = models.ManyToManyField(CmPreparationDisplayStage, related_name='stage_ids')
    is_archived = models.BooleanField(default=False)

    @property
    def OrderCount(self):
        return "Total Orders in Display"
    


class CmKdsOrder(models.Model):

    id = models.AutoField(primary_key=True)
    group_id = models.UUIDField(default=uuid4, editable=False)
    cm_pos_order = models.ForeignKey(CmOrders, related_name='kds_order', on_delete=models.DO_NOTHING, null=True)
    cm_preparation_display = models.ForeignKey(CmPreparationDisplay, related_name='order_preparation_display', on_delete=models.DO_NOTHING, null=True)
    cm_preparation_display_stage = models.ForeignKey(CmPreparationDisplayStage, related_name='order_preparation_display_display', on_delete=models.DO_NOTHING, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=True)
    sequence = models.IntegerField(null=True)
    status = models.CharField(default="New")
    cancelled = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)


class CmKdsOrderline(models.Model):

    id = models.AutoField(primary_key=True)
    cm_kds_order = models.ForeignKey(CmKdsOrder, related_name='kds_order_orderline', on_delete=models.DO_NOTHING, null=True)
    cm_pos_orderline = models.ForeignKey(CmOrderLine, related_name='kds_orderline', on_delete=models.DO_NOTHING, null=True)
    is_done = models.BooleanField(default=False)
    quantity_cancelled = models.FloatField(default=0.0)
    suiteCommande = models.BooleanField(default=False)
    suiteOrdred = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now_add=True)
    combo_prod_ids = models.ManyToManyField('products.ProductVariant', related_name='combo_prod_ids')
    is_archived = models.BooleanField(default=False)
