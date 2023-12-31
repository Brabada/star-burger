# Generated by Django 3.2.15 on 2023-10-28 00:31

from django.db import migrations
from django.db.models import Sum, F
from decimal import Decimal


def fill_empty_orders_prices(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    order_items = OrderItem.objects.\
        filter(price=Decimal(0)).\
        select_related('product'). \
        annotate(full_price=Sum(F('product__price') * F('quantity')))
    if order_items.exists():
        for order_item in order_items:
            order_item.price = Decimal(order_item.full_price).quantize(Decimal(1.0))
            print(order_item.price)
            order_item.save()


def empty_orders_prices(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    OrderItem.objects.exclude(price=Decimal(0)).update(price=Decimal(0))
class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0041_auto_20231028_0330'),
    ]

    operations = [
        migrations.RunPython(fill_empty_orders_prices, empty_orders_prices)
    ]
