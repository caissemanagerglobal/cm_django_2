# pos/models.py
from django.db import models
from users.models import CmEmployees
from django.db.models import Sum
from payments.models import CmPayments, CmClosingBalances


class CmDays(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    opening_time = models.DateTimeField(null=True)
    closing_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=255)
    opening_employee = models.ForeignKey(CmEmployees, related_name='day_opening_employee', on_delete=models.DO_NOTHING)
    closing_employee = models.ForeignKey(CmEmployees, related_name='day_closing_employee', on_delete=models.DO_NOTHING, null=True)
    revenue_system = models.FloatField(default=0.0)
    revenue_declared = models.FloatField(default=0.0)
    is_archived = models.BooleanField(default=False)

    @property
    def revenueSystem(self):
        total_revenue = CmPayments.objects.filter(cm_shift__cm_day=self).aggregate(
            total=Sum('amount')
        )['total'] or 0.0

        return total_revenue

    @property
    def revenueDeclared(self):
        total_declared = CmClosingBalances.objects.filter(cm_shift__cm_day=self).aggregate(
            total=Sum('cashier_amount')
        )['total'] or 0.0

        return total_declared


class CmPos(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    printer_ip = models.CharField(max_length=255, null=True)
    is_archived = models.BooleanField(default=False)

class CmFloor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

class CmTable(models.Model):
    id = models.AutoField(primary_key=True)
    floor = models.ForeignKey(CmFloor, related_name='floor', on_delete=models.DO_NOTHING, default=1)
    name = models.CharField(max_length=255)
    seats = models.IntegerField(null=True)
    position_h = models.FloatField(null=True)
    position_v = models.FloatField(null=True)
    status = models.CharField(max_length=255,null=True)
    width = models.FloatField(null=True)
    height = models.FloatField(null=True)
    is_archived = models.BooleanField(default=False)


class CmShifts(models.Model):
    id = models.AutoField(primary_key=True)
    cm_day = models.ForeignKey(CmDays, related_name='day_shifts', on_delete=models.DO_NOTHING)
    cm_pos = models.ForeignKey(CmPos, related_name='pos_shifts', on_delete=models.DO_NOTHING)
    cm_employee = models.ForeignKey(CmEmployees, related_name='employee_shifts', on_delete=models.DO_NOTHING)
    opening_time = models.DateTimeField(null=True)
    closing_time = models.DateTimeField(null=True)
    starting_balance = models.FloatField()
    status = models.CharField(max_length=255,null=True)
    cashdraw_number = models.IntegerField(null=True)
    is_archived = models.BooleanField(default=False)

    # @property
    # def closingBalance(self):
    #     return "the closing balance calculation logic" 