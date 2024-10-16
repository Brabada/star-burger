# Generated by Django 3.2.15 on 2024-10-01 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0002_auto_20231124_0110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='latitude',
            field=models.DecimalField(decimal_places=6, max_digits=9, verbose_name='широта'),
        ),
        migrations.AlterField(
            model_name='place',
            name='longitude',
            field=models.DecimalField(decimal_places=6, max_digits=9, verbose_name='долгота'),
        ),
    ]
