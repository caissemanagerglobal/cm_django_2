# Generated by Django 5.0.7 on 2024-08-16 16:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CmFloor',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('is_archived', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CmPos',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('printer_ip', models.CharField(max_length=255, null=True)),
                ('is_archived', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CmDays',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('opening_time', models.DateTimeField(null=True)),
                ('closing_time', models.DateTimeField(null=True)),
                ('status', models.CharField(max_length=255)),
                ('revenue_system', models.FloatField(default=0.0)),
                ('revenue_declared', models.FloatField(default=0.0)),
                ('is_archived', models.BooleanField(default=False)),
                ('closing_employee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='day_closing_employee', to='users.cmemployees')),
                ('opening_employee', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='day_opening_employee', to='users.cmemployees')),
            ],
        ),
        migrations.CreateModel(
            name='CmShifts',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('opening_time', models.DateTimeField(null=True)),
                ('closing_time', models.DateTimeField(null=True)),
                ('starting_balance', models.FloatField()),
                ('status', models.CharField(max_length=255, null=True)),
                ('cashdraw_number', models.IntegerField(null=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('cm_day', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='day_shifts', to='pos.cmdays')),
                ('cm_employee', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='employee_shifts', to='users.cmemployees')),
                ('cm_pos', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='pos_shifts', to='pos.cmpos')),
            ],
        ),
        migrations.CreateModel(
            name='CmTable',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('seats', models.IntegerField(null=True)),
                ('position_h', models.FloatField(null=True)),
                ('position_v', models.FloatField(null=True)),
                ('status', models.CharField(max_length=255, null=True)),
                ('width', models.FloatField(null=True)),
                ('height', models.FloatField(null=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('floor', models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='floor', to='pos.cmfloor')),
            ],
        ),
    ]