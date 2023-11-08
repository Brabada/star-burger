# Generated by Django 3.2.15 on 2023-11-08 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0047_auto_20231107_2245'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('PAID_BY_SITE', 'Оплачен через сайт'), ('UNPAID_BY_SITE', 'Не оплачен через сайт'), ('CASH_ON_DELIVERY', 'Наличными при вручении'), ('CASHLESS_ON_DELIVERY', 'Электронно при вручении')], db_index=True, default='UNPAID_BY_SITE', max_length=50, verbose_name='Способ оплаты'),
        ),
    ]
