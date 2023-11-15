# Generated by Django 3.2.15 on 2023-11-15 21:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_order_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='foodcartapp.restaurant', verbose_name='Ресторан для готовки заказа'),
        ),
    ]
