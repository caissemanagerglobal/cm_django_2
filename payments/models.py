# payments/models.py
from django.db import models 
from users.models import CmClients, CmEmployees
from orders.models import CmOrders

class CmPaymentMethods(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    image = models.BinaryField(null=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='sub_methods', on_delete=models.DO_NOTHING)
    in_situation = models.BooleanField()
    is_tpe = models.BooleanField(default=False)
    is_cash = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

class CmPaymentMethodsAttributes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    payment_method = models.ForeignKey(CmPaymentMethods, related_name='payment_method_attributte', on_delete=models.DO_NOTHING)
    in_form = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)


class CmClosingBalances(models.Model):
    id = models.AutoField(primary_key=True)
    cm_payment_method = models.ForeignKey(CmPaymentMethods, related_name='closing_balances', on_delete=models.DO_NOTHING)
    cm_shift = models.ForeignKey('pos.CmShifts', related_name='closing_balances', on_delete=models.DO_NOTHING)
    system_amount = models.FloatField()
    cashier_amount = models.FloatField()
    verification_amount = models.FloatField(default=0.0)
    verification_employee = models.ForeignKey(CmEmployees, related_name='closing_ver_employee', on_delete=models.DO_NOTHING, null=True)
    is_archived = models.BooleanField(default=False)

class CmPayments(models.Model):
    id = models.AutoField(primary_key=True)
    cm_shift = models.ForeignKey('pos.CmShifts', related_name='shift', on_delete=models.DO_NOTHING)
    cm_order = models.ForeignKey(CmOrders, related_name='payments', on_delete=models.DO_NOTHING)
    amount = models.FloatField()
    cm_payment_method = models.ForeignKey(CmPaymentMethods, related_name='payments', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(default="paid")
    is_archived = models.BooleanField(default=False)

class CmPaymentsAttribute(models.Model):
    id = models.AutoField(primary_key=True)
    payment = models.ForeignKey(CmPayments, related_name='payment_attribute', on_delete=models.DO_NOTHING)
    payment_method_attribute = models.ForeignKey(CmPaymentMethodsAttributes, related_name='payment_method_attribute', on_delete=models.DO_NOTHING)
    value = models.CharField(null=True)
    is_archived = models.BooleanField(default=False)

class CmClientDebts(models.Model):
    id = models.AutoField(primary_key=True)
    cm_client = models.ForeignKey(CmClients, related_name='client_debts', on_delete=models.DO_NOTHING)
    cm_shift = models.ForeignKey('pos.CmShifts', related_name='client_debts', on_delete=models.DO_NOTHING)
    amount = models.FloatField()
    is_refund = models.BooleanField()
    cm_payment_method = models.ForeignKey(CmPaymentMethods, related_name='client_debts', on_delete=models.DO_NOTHING)
    cm_payment = models.ForeignKey(CmPayments, related_name='client_debts', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)


class CmDrops(models.Model):
    id = models.AutoField(primary_key=True)
    amount = models.FloatField()
    datetime = models.DateTimeField(auto_now_add=True)
    positive = models.BooleanField(default=False)
    cm_shift = models.ForeignKey('pos.CmShifts', related_name='drops', on_delete=models.DO_NOTHING)
    cm_employee = models.ForeignKey(CmEmployees, related_name='drops', on_delete=models.DO_NOTHING)
    comment = models.CharField()
    is_archived = models.BooleanField(default=False)