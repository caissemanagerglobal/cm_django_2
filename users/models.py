from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password

class CmFeature(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

class CmRole(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    cm_features = models.ManyToManyField(CmFeature, related_name="role_features")
    is_archived = models.BooleanField(default=False)

class CmEmployees(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    has_pos = models.BooleanField(default=True)
    cm_role = models.ForeignKey(CmRole, related_name='employees', on_delete=models.DO_NOTHING)
    pin_code = models.CharField(max_length=255)
    badge_number = models.CharField(max_length=255, null=True)
    poste = models.CharField(max_length=255, null=True)
    preparation_display = models.ForeignKey('kds.CmPreparationDisplay', related_name='employee_preparation_display', on_delete=models.DO_NOTHING, null=True)
    last_login_time = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.pin_code = make_password(self.pin_code)
        super().save(*args, **kwargs)

class CmClients(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    telephone = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    is_archived = models.BooleanField(default=False)