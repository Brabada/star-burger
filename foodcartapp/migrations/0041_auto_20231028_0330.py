# Generated by Django 3.2.15 on 2023-10-28 00:30

from decimal import Decimal
from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0040_rename_name_order_firstname'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='order',
            managers=[
                ('info', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=9, verbose_name='стоимость позиции'),
        ),
    ]
