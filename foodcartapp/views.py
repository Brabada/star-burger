from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from phonenumber_field.validators import validate_international_phonenumber

from .models import Product, Order, OrderItem



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


def validate_register_form_field(field_name, field_type, form):
    content = ''
    if field_name in form:
        if isinstance(form[field_name], field_type):
            if not form[field_name]:
                content = {'error': f'{field_name} is empty'}
        else:
            content = {'error': f'{field_name} key contains null or not a {field_type} type'}
    else:
        content = {'error': f'{field_name} key is not represented'}
    if content:
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    else:
        return


@api_view(['POST'])
def register_order(request):
    order_form = request.data
    dumped_products = []

    # validation
    for field in ('firstname', 'lastname', 'address', 'phonenumber'):
        response = validate_register_form_field(field, str, order_form)
        if response:
            return response

    # additional validation for phonenumber and products
    try:
        validate_international_phonenumber(order_form['phonenumber'])
    except ValidationError:
        return Response({'error': 'incorrect phonenumber field format'}, status=status.HTTP_400_BAD_REQUEST)

    # products key validation
    response = validate_register_form_field('products', list, order_form)
    if response:
        return response

    for product in order_form['products']:
        product_id = product['product']
        try:
            fetched_product = Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response({'error': 'product key with id not found'}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'error': 'there is multiple products with received id'}, status=status.HTTP_409_CONFLICT)
        dumped_products.append(
            {
                'product': fetched_product,
                'quantity': product['quantity'],
            }
        )

    order = Order(
        name=order_form['firstname'],
        lastname=order_form['lastname'],
        phonenumber=order_form['phonenumber'],
        address=order_form['address'],
    )

    order.save()
    for product in dumped_products:
        order_item = OrderItem(
            product=product['product'],
            quantity=product['quantity'],
            order=order,
        )
        order_item.save()

    return Response({})
