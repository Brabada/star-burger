from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum, F, Case, Value, When
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=300,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def total_price(self):
        return self.annotate(order_price=Sum(F('order_items__price')))

    def order_by_priority(self):
        priority_order = Case(
            When(status=Order.UNPROCESSED, then=Value(1)),
            When(status=Order.ASSEMBLY, then=Value(2)),
            When(status=Order.DELIVERY, then=Value(3)),
            When(status=Order.DONE, then=Value(4)),
        )
        return self.alias(priority_order=priority_order).order_by('priority_order', 'id')


class Order(models.Model):
    firstname = models.CharField(
        'имя',
        max_length=50,
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50,
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        'номер телефона',
        max_length=15,
    )
    address = models.TextField('адрес доставки', max_length=350)

    UNPROCESSED = 'UNPROCESSED'
    ASSEMBLY = 'ASSEMBLY'
    DELIVERY = 'DELIVERY'
    DONE = 'DONE'
    STATUS_CHOICES = [
        (UNPROCESSED, 'Необработанный'),
        (ASSEMBLY, 'Готовится'),
        (DELIVERY, 'Доставляется'),
        (DONE, 'Исполнен'),
    ]
    status = models.CharField(
        'статус заказа',
        max_length=50,
        choices=STATUS_CHOICES,
        default=UNPROCESSED,
        db_index=True,
    )

    PAID_BY_SITE = 'PAID_BY_SITE'
    UNPAID_BY_SITE = 'UNPAID_BY_SITE'
    CASH_ON_DELIVERY = 'CASH_ON_DELIVERY'
    CASHLESS_ON_DELIVERY = 'CASHLESS_ON_DELIVERY'
    PAYMENT_CHOICES = [
        (PAID_BY_SITE, 'Оплачен через сайт'),
        (UNPAID_BY_SITE, 'Не оплачен через сайт'),
        (CASH_ON_DELIVERY, 'Наличными при получении'),
        (CASHLESS_ON_DELIVERY, 'Электронно при получении'),
    ]
    payment_method = models.CharField(
        'Способ оплаты',
        choices=PAYMENT_CHOICES,
        default=UNPAID_BY_SITE,
        db_index=True,
        max_length=50,
    )

    registered_at = models.DateTimeField(
        'Зарегистрирован',
        blank=True,
        default=timezone.now,
        db_index=True,
    )

    called_at = models.DateTimeField(
        'Когда позвонили',
        null=True,
        blank=True,
    )

    delivered_at = models.DateTimeField(
        'Доставлен',
        null=True,
        blank=True,
    )

    comment = models.TextField(
        'Комментарий к заказу',
        blank=True,
    )

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Ресторан для готовки заказа',
    )

    info = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.lastname} {self.firstname}, {self.address}'


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='продукт',
        related_name='order_items',
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name='заказ',
        related_name='order_items',
    )

    price = models.DecimalField(
        'стоимость позиции',
        validators=[MinValueValidator(Decimal(0))],
        default=Decimal(0),
        max_digits=9,
        decimal_places=2,
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f'{self.quantity} - {self.product}'
