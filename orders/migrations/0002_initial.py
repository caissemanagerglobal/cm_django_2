# Generated by Django 5.0.7 on 2024-08-16 16:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('orders', '0001_initial'),
        ('pos', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cmorders',
            name='cm_shift',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_shift', to='pos.cmshifts'),
        ),
        migrations.AddField(
            model_name='cmorders',
            name='cm_table',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_table', to='pos.cmtable'),
        ),
        migrations.AddField(
            model_name='cmorders',
            name='cm_waiter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='orders', to='users.cmemployees'),
        ),
        migrations.AddField(
            model_name='cmorders',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_orders', to='users.cmemployees'),
        ),
        migrations.AddField(
            model_name='cmorders',
            name='delivery_guy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='delivery_guy', to='users.cmemployees'),
        ),
        migrations.AddField(
            model_name='cmorders',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='updated_orders', to='users.cmemployees'),
        ),
        migrations.AddField(
            model_name='cmorderline',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_lines', to='orders.cmorders'),
        ),
        migrations.AddField(
            model_name='cmordertype',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='orders.cmordertype'),
        ),
        migrations.AddField(
            model_name='cmorders',
            name='cm_order_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='orders', to='orders.cmordertype'),
        ),
        migrations.AddField(
            model_name='cmorderline',
            name='cm_order_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_lines', to='orders.cmordertype'),
        ),
        migrations.AddField(
            model_name='discounts',
            name='discount_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='discount_discount_type', to='core.discounttype'),
        ),
        migrations.AddField(
            model_name='discounts',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='discounts', to='orders.cmorders'),
        ),
        migrations.AddField(
            model_name='discounts',
            name='orderline',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='discounts', to='orders.cmorderline'),
        ),
        migrations.AddField(
            model_name='ordercancel',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='users.cmemployees'),
        ),
        migrations.AddField(
            model_name='ordercancel',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='cancellations', to='orders.cmorders'),
        ),
        migrations.AddField(
            model_name='ordercancel',
            name='orderline',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='cancellations', to='orders.cmorderline'),
        ),
    ]
