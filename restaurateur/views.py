import logging
from decimal import Decimal

from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Product, Restaurant, RestaurantMenuItem, Order, OrderItem
from places.models import Place


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):

    queryset_order_item = OrderItem.objects.select_related('product')
    prefetched_order_items = Prefetch('order_items', queryset=queryset_order_item)
    orders = Order.info.total_price()\
        .select_related('restaurant')\
        .prefetch_related(
            prefetched_order_items,)\
        .order_by_priority()\
        .exclude(status=Order.DONE)

    all_restaurants = Restaurant.objects.prefetch_related(
                Prefetch('menu_items', RestaurantMenuItem.objects.select_related('product').filter(availability=True)))

    places = Place.objects.values('address', 'longitude', 'latitude').order_by('address')

    view_order_items = []
    for order in orders:
        view_order_item = {
            'order_item': order,
        }

        # if order not designated to restaurant
        if not order.restaurant:
            order_products = set()
            for order_item in order.order_items.all():
                order_products.add(order_item.product)

            # comparing products set with restaurants available products
            available_restaurants = []
            for restaurant in all_restaurants:
                restaurant_products = set()
                for menu_item in restaurant.menu_items.all():
                    restaurant_products.add(menu_item.product)
                if order_products.issubset(restaurant_products):
                    available_restaurants.append(restaurant)

            # evaluate distance between client and available restaurants
            restaurants = []
            client_coordinates = next(
                (coords['longitude'], coords['latitude']) for coords in places if coords['address'] == order.address
            )
            # Making list of pairs of available restaurant and distance from restaurant to client
            for restaurant in available_restaurants:
                distance_to_restaurant = None
                if client_coordinates[0] != Decimal(0) and client_coordinates[1] != Decimal(0):
                    restaurant_coordinates = next(
                        (coords['longitude'], coords['latitude'])
                        for coords in places if coords['address'] == restaurant.address
                    )

                    distance_to_restaurant = distance.distance(
                        (client_coordinates[0], client_coordinates[1]),
                        (restaurant_coordinates[0], restaurant_coordinates[1])
                    ).km

                    logging.debug(
                        f'Distance to client {order.address} from resto {restaurant.address}: {distance_to_restaurant}')

                    if distance_to_restaurant:
                        distance_to_restaurant = round(Decimal(distance_to_restaurant), 3)
                restaurants.append(
                    {
                        'restaurant': restaurant,
                        'distance': distance_to_restaurant
                    }
                )
            view_order_item['restaurants'] = sorted(restaurants, key=lambda restaurant: restaurant['distance'])
            view_order_items.append(view_order_item)
        else:
            view_order_items.append(view_order_item)

    return render(request, template_name='order_items.html', context={
        'order_items': view_order_items,
    })
