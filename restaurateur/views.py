from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from decimal import Decimal
from geopy import distance

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from places.models import Place
from places.views import fetch_coordinates
import datetime


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

    orders = Order.info.total_price()\
        .prefetch_related('order_items__product__menu_items__restaurant')\
        .order_by_priority()\
        .exclude(status=Order.DONE)

    # 1. Order->order_items->all OrderItems for Order
    # 2. for OrderItem->by product-> gets all RestaurantMenuItem(with availability=True)
    # 3. RestaurantMenuItem -> Restaurants -> saving Restaurants for each OrderItem
    # 4. Gets intersection between restaurants sets from OrderItems in Order and saving restaurants if have any

    view_order_items = []
    for order in orders:
        view_order_item = {
            'order_item': order,
        }

        # only for order without selected restaurant
        if not order.restaurant:
            order_items = order.order_items.all()
            order_restaurants = []
            for order_item in order_items:
                menu_items = RestaurantMenuItem.objects\
                    .select_related('restaurant')\
                    .filter(product=order_item.product, availability=True)
                order_restaurants.append({menu_item.restaurant for menu_item in menu_items})
            available_restaurants = set.intersection(*order_restaurants)
            # get place by address
            # if place not found - fetch_coordinates by address and create place with address and coords
            # if place founded - take from place coords for eval distance
            try:
                place = Place.objects.get(address=order.address)
                client_coordinates = place.latitude, place.longitude
            except ObjectDoesNotExist:
                client_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API_KEY, order.address)
                if not client_coordinates:
                    client_coordinates = Decimal(0), Decimal(0)
                Place.objects.create(
                    address=order.address,
                    latitude=client_coordinates[0],
                    longitude=client_coordinates[1],
                    last_request=datetime.date.today(),
                )

            restaurants = []
            # Making list of pairs of available restaurant and distance from restaurant to client
            for restaurant in available_restaurants:
                distance_to_client = None
                if client_coordinates:
                    try:
                        place = Place.objects.get(address=restaurant.address)
                        restaurant_coordinates = place.latitude, place.longitude
                    except ObjectDoesNotExist:
                        restaurant_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API_KEY, restaurant.address)
                        if not restaurant_coordinates:
                            restaurant_coordinates = Decimal(0), Decimal(0)
                        Place.objects.create(
                            address=restaurant.address,
                            latitude=restaurant_coordinates[0],
                            longitude=restaurant_coordinates[1],
                            last_request=datetime.date.today(),
                        )
                    distance_to_client = distance.distance(
                        distance.lonlat(*client_coordinates),
                        distance.lonlat(*restaurant_coordinates)).km
                    print(f'Distance to client {order.address} from resto {restaurant.address}: {distance_to_client}')
                    if distance_to_client:
                        distance_to_client = round(Decimal(distance_to_client), 3)
                restaurants.append(
                    {
                        'restaurant': restaurant,
                        'distance': distance_to_client
                    }
                )
            view_order_item['restaurants'] = sorted(restaurants, key=lambda restaurant: restaurant['distance'])
            view_order_items.append(view_order_item)
        else:
            view_order_items.append(view_order_item)

    return render(request, template_name='order_items.html', context={
        'order_items': view_order_items,
    })
