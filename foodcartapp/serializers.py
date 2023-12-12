from decimal import Decimal

from django.shortcuts import get_object_or_404
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.serializers import ModelSerializer

from .models import Order, OrderItem, Product


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)
    phonenumber = PhoneNumberField(region='RU')

    def create(self, validated_data):
        order = Order(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            phonenumber=validated_data['phonenumber'],
            address=validated_data['address'],
        )
        order.save()

        order_items = []
        for product in validated_data['products']:
            product_id = product['product'].id
            product_price = get_object_or_404(Product.objects.values('price'), id=product_id)
            print(product_price)
            order_items.append(
                OrderItem(
                    **product,
                    order=order,
                    price=Decimal(product_price['price'] * product['quantity'])
                )
            )

        OrderItem.objects.bulk_create(order_items)
        return order

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']
