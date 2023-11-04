from django.http import JsonResponse
from django.templatetags.static import static
from django.shortcuts import get_object_or_404
from django.db.transaction import atomic
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Product, Order, OrderItem

from decimal import Decimal


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


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']


#{"products":
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
    dumped_products = []
    for product in serializer.validated_data['products']:
        product_id = product['product'].id
        fetched_product = get_object_or_404(Product, id=product_id)

        dumped_products.append(
            {
                'product': fetched_product,
                'quantity': product['quantity'],
                'price': Decimal(fetched_product.price * product['quantity']),
            }
        )

    order = Order(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address'],
    )
    order.save()
    for product in dumped_products:
        order_item = OrderItem(
            product=product['product'],
            quantity=product['quantity'],
            order=order,
            price=product['price'],
        )
        order_item.save()

    # Serializing Order and return for frontend
    serializer = OrderSerializer(order)
    return Response(serializer.data)
