import datetime
import logging.handlers
from decimal import Decimal

from django.conf import settings
from django.db.transaction import atomic
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response

from places.models import Place
from places.views import fetch_coordinates, create_restaurant_places_if_not_exists
from .models import Product
from .serializers import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()
    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


# {"products":
# [{"product": 2, "quantity": 3}, {"product": 1, "quantity": 3}],
# "firstname": "Максим",
# "lastname": "Булкович",
# "phonenumber": "+79653333333",
# "address": "Пушкина Колотушкина
# "}


@atomic()
@api_view(['POST'])
def register_order(request):
    # Deserializing order form
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = serializer.save()

    place_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API_KEY, order.address)
    if not place_coordinates:
        place_coordinates = Decimal(0), Decimal(0)

    place, created = Place.objects.get_or_create(
        address=order.address,
        defaults={
            'longitude': place_coordinates[1],
            'latitude': place_coordinates[0],
            'last_request': datetime.date.today(),
        }
    )
    logging.DEBUG(f"Place {place} was created?{created}")

    create_restaurant_places_if_not_exists()

    # Serializing Order and return for frontend
    serializer = OrderSerializer(order)
    return Response(serializer.data)
