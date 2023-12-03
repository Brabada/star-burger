import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import ObjectDoesNotExist

from foodcartapp.models import Restaurant
from .models import Place


def create_restaurant_places_if_not_exists():
    restaurants_addresses = Restaurant.objects.all().values('address')
    for address in restaurants_addresses:
        try:
            Place.objects.get(address=address)
        except ObjectDoesNotExist:
            restaurants_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API_KEY, address=address)
            if not restaurants_coordinates:
                restaurants_coordinates = Decimal(0), Decimal(0)
            Place.objects.create(
                address=address,
                longitude=restaurants_coordinates[1],
                latitude=restaurants_coordinates[0],
                last_request=datetime.date.today(),
            )


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat
