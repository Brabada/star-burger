# Generated by Django 3.2.15 on 2023-11-07 19:45

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_order_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Когда позвонили'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Доставлен'),
        ),
        migrations.AddField(
            model_name='order',
            name='registered_at',
            field=models.DateTimeField(blank=True, db_index=True, default=django.utils.timezone.now, verbose_name='Зарегистрирован'),
        ),
    ]
