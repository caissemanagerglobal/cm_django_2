from django.db import models

class SiteSettings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    if_val = models.CharField(max_length=255, null=True)
    ice_val = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    slogan = models.CharField(max_length=255, null=True)
    image = models.CharField(max_length=255, null=True)
    wifi_password = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    message = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.CmEmployees', related_name='created_site_settings', on_delete=models.DO_NOTHING)
    updated_by = models.ForeignKey('users.CmEmployees', related_name='updated_site_settings', on_delete=models.DO_NOTHING)
    is_archived = models.BooleanField(default=False)

class ConfigSettings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.CmEmployees', related_name='created_config_settings', on_delete=models.DO_NOTHING)
    updated_by = models.ForeignKey('users.CmEmployees', related_name='updated_config_settings', on_delete=models.DO_NOTHING)
    is_archived = models.BooleanField(default=False)

class Tax(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(null=True, max_length=255)
    value = models.FloatField(null=True)
    is_archived = models.BooleanField(default=False)

class DiscountType(models.Model):
    TYPE_CHOICES = [
        ('amount', 'Amount'),
        ('percentage', 'Percentage')
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(null=True, max_length=255,choices=TYPE_CHOICES)
    value = models.FloatField(null=True)
    is_archived = models.BooleanField(default=False)


class DefinedNotes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)