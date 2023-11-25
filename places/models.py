from django.db import models
from decimal import Decimal


class Place(models.Model):
    address = models.TextField(
        'адрес места',
        max_length=350,
        unique=True,
    )
    longitude = models.DecimalField(
        'долгота',
        max_digits=9,
        decimal_places=6,
        default=Decimal(0),
    )
    latitude = models.DecimalField(
        'широта',
        max_digits=9,
        decimal_places=6,
        default=Decimal(0),
    )
    last_request = models.DateField(
        'дата последнего запроса к геокодеру',
        null=True,
    )

    class Meta:
        verbose_name = 'место'
        verbose_name_plural = 'места'

    def __str__(self):
        return f'{self.address}'
