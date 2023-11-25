from django.contrib import admin
from .models import Place

# Register your models here.

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        'address',
        'longitude',
        'latitude',
        'last_request',
    )
