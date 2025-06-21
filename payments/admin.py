# ===== File: payments/admin.py =====

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Governorate,
    City,
    Customer,
    Driver,
    Vehicle,
    Route,
    Trip,
    Payment,
    CustomerWallet,
    DriverWallet,
    NFCCard,
    Transfer,
    Device,
    DeviceLocation,
)

@admin.register(CustomerWallet)
class CustomerWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'balance')
    search_fields = ('customer__name',)

@admin.register(DriverWallet)
class DriverWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'balance', 'pending_balance')
    search_fields = ('driver__name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'national_id', 'phone',
        'email', 'governorate', 'city', 'is_active'
    )
    list_filter = ('governorate', 'city', 'is_active')
    search_fields = ('name', 'national_id', 'phone', 'email')

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'uid', 'name', 'national_id', 'phone',
        'email', 'license_number', 'governorate',
        'city', 'in_zone', 'driver_photo_thumb',
        'license_photo_thumb'
    )
    list_filter = ('governorate', 'city', 'in_zone')
    search_fields = (
        'name', 'national_id', 'phone',
        'email', 'license_number'
    )
    readonly_fields = ('driver_photo_thumb', 'license_photo_thumb')

    def driver_photo_thumb(self, obj):
        if obj.driver_photo:
            return format_html(
                '<img src="{}" style="max-height:60px;"/>',
                obj.driver_photo.url
            )
        return "-"
    driver_photo_thumb.short_description = 'Driver Photo'

    def license_photo_thumb(self, obj):
        if obj.license_photo:
            return format_html(
                '<img src="{}" style="max-height:60px;"/>',
                obj.license_photo.url
            )
        return "-"
    license_photo_thumb.short_description = 'License Photo'

@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'governorate')
    list_filter = ('governorate',)
    search_fields = ('name',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'driver')
    list_filter = ('driver__governorate', 'driver__city')
    search_fields = ('number', 'driver__name')

# @admin.register(Route)
# class RouteAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'city')
#     list_filter = ('city__governorate', 'city')
#     search_fields = ('name',)

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'driver', 'vehicle', 'route',
        'date', 'sequence_number', 'start_time',
        'end_time', 'in_zone','get_paid_passengers',
    )

    @admin.display(description='Number of fees paid')
    def get_paid_passengers(self, obj):
        return Payment.objects.filter(trip=obj).count()

    list_filter = ('date', 'driver', 'route', 'in_zone')
    search_fields = ('driver__name', 'vehicle__number')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer', 'trip', 'fare',
        'new_balance', 'timestamp', 'payment_method'
    )
    list_filter = ('payment_method', 'timestamp')
    search_fields = ('customer__name', 'trip__driver__name')

@admin.register(NFCCard)
class NFCCardAdmin(admin.ModelAdmin):
    list_display = ('uid', 'customer')
    search_fields = ('uid', 'customer__name')

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    pass

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(DeviceLocation)
class DeviceLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'device', 'latitude', 'longitude', 'timestamp')
    search_fields = ('device__name',)



# payments/admin.py

from .models import Stop

class StopInline(admin.TabularInline):
    model = Stop
    extra = 1

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    exclude = (
        'name',
        'start_stop_name', 'start_latitude', 'start_longitude',
        'end_stop_name',   'end_latitude',   'end_longitude',
    )
    list_display = ('id', 'display_name', 'city')
    inlines      = [StopInline]