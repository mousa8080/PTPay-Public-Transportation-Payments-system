# File: payments/serializers.py

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.hashers import make_password


from .models import (
    Governorate, City, Customer, Driver,
    Vehicle, Route, Trip, NFCCard,
    Transfer, Payment, DeviceLocation,
    CustomerWallet, DriverWallet,Stop,
)

# ============================
# Serializer for Governorate
# ============================
class GovernorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Governorate
        fields = '__all__'


# ============================
# Serializer for City
# ============================
class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


# ============================
# Serializer for Customer (Passenger)
# ============================
class CustomerSerializer(serializers.ModelSerializer):
    balance    = SerializerMethodField()
    governorate = serializers.PrimaryKeyRelatedField(
        queryset=Governorate.objects.all(),
        required=False,
        allow_null=True
    )
    city        = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model  = Customer
        fields = '__all__'

    def get_balance(self, obj):
        return obj.wallet.balance

    def validate_national_id(self, value):
        if len(value) != 14 or not value.isdigit():
            raise serializers.ValidationError("الرقم القومي يجب أن يكون 14 رقماً")
        if Driver.objects.filter(national_id=value).exists():
            raise serializers.ValidationError("الرقم القومي مسجل بالفعل كسائق")
        return value

    def validate_phone(self, value):
        if len(value) != 11 or not value.isdigit():
            raise serializers.ValidationError("رقم الهاتف يجب أن يكون 11 رقماً")
        if Driver.objects.filter(phone=value).exists():
            raise serializers.ValidationError("رقم الهاتف مسجل بالفعل كسائق")
        return value

    def create(self, validated_data):
        pwd = validated_data.pop('password', None)
        if pwd:
            validated_data['password'] = make_password(pwd)
        return super().create(validated_data)


# ============================
# Serializer for Driver
# ============================
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.contrib.auth.hashers import make_password

from .models import Driver, Governorate, City, Route, Customer

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.contrib.auth.hashers import make_password

from .models import Driver, Governorate, City, Route, Customer

class DriverSerializer(serializers.ModelSerializer):
    assigned_route      = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all(),
        required=False,
        allow_null=True
    )
    assigned_route_name = SerializerMethodField()
    vehicles            = SerializerMethodField()
    governorate         = serializers.PrimaryKeyRelatedField(
        queryset=Governorate.objects.all(),
        required=False,
        allow_null=True
    )
    city                = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Driver
        fields = [
            'id',
            'name', 'national_id', 'phone', 'email',
            'password', 'license_number',
            'driver_photo', 'license_photo',
            'governorate', 'city', 'in_zone',
            'assigned_device', 'assigned_route',
            'assigned_route_name', 'vehicles',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'in_zone':   {'read_only': True},
            'assigned_device': {'read_only': True},
        }
        read_only_fields = (
            'in_zone',
            'assigned_route_name',
            'vehicles',
            'assigned_device',
        )

    def get_assigned_route_name(self, obj):
        return obj.assigned_route.display_name if obj.assigned_route else None

    def get_vehicles(self, obj):
        return [v.id for v in obj.vehicles.all()]

    def validate_national_id(self, value):
        if len(value) != 14 or not value.isdigit():
            raise serializers.ValidationError("يجب أن يكون 14 رقمًا")
        if Customer.objects.filter(national_id=value).exists():
            raise serializers.ValidationError("مسجل بالفعل كعميل")
        return value

    def validate_phone(self, value):
        if len(value) != 11 or not value.isdigit():
            raise serializers.ValidationError("يجب أن يكون 11 رقمًا")
        if Customer.objects.filter(phone=value).exists():
            raise serializers.ValidationError("مسجل بالفعل كعميل")
        return value

    def create(self, validated_data):
        pwd = validated_data.pop('password', None)
        if pwd:
            validated_data['password'] = make_password(pwd)
        return super().create(validated_data)

# ============================
# Serializer for Vehicle
# ============================
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Vehicle
        fields = '__all__'



class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Stop
        fields = ['id', 'name', 'min_lat', 'min_lng', 'max_lat', 'max_lng']




# ============================
# Serializer for Route
# ============================
class RouteSerializer(serializers.ModelSerializer):
    stops        = StopSerializer(many=True, read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model  = Route
        fields = ['id', 'city', 'stops', 'display_name']

    def get_display_name(self, obj):
        return obj.display_name
# ============================
# Serializer for Trip (with nested route & vehicle)
# ============================
class TripSerializer(serializers.ModelSerializer):
    route             = RouteSerializer(read_only=True)
    vehicle           = VehicleSerializer(read_only=True)
    route_name        = SerializerMethodField()
    start_stop_name   = SerializerMethodField()
    end_stop_name     = SerializerMethodField()
    vehicle_number    = SerializerMethodField()
    start_time_iso    = SerializerMethodField()
    paid_passengers   = SerializerMethodField()

    class Meta:
        model  = Trip
        fields = '__all__'

    def get_route_name(self, obj):
        return obj.route.display_name if obj.route else None

    def get_start_stop_name(self, obj):
        stops = obj.route.stops.all()
        return stops[0].name if stops else None

    def get_end_stop_name(self, obj):
        stops = obj.route.stops.all()
        return stops.last().name if stops else None

    def get_vehicle_number(self, obj):
        return obj.vehicle.number if obj.vehicle else None

    def get_start_time_iso(self, obj):
        return obj.start_time.isoformat() if obj.start_time else None

    def get_paid_passengers(self, obj):
        return obj.payment_set.count()


# ============================
# Serializer for CustomerWallet
# ============================
class CustomerWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomerWallet
        fields = '__all__'


# ============================
# Serializer for DriverWallet
# ============================
class DriverWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DriverWallet
        fields = '__all__'


# ============================
# Serializer for NFC Card
# ============================
class NFCCardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NFCCard
        fields = '__all__'


# ============================
# Serializer for Transfer
# ============================
class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Transfer
        fields = '__all__'


# ============================
# Serializer for Payment  (بعد التعديل)
# ============================
class PaymentSerializer(serializers.ModelSerializer):
    # ❶ للقراءة فقط: يُرجع تفاصيل الرحلة (كما كان) حتى لا يكسر الـ Flutter
    trip = TripSerializer(read_only=True)

    # ❷ للكتابة فقط: نستقبل trip_id ويُخزَّن في نفس الحقل الحقيقي trip
    trip_id = serializers.PrimaryKeyRelatedField(
        queryset=Trip.objects.all(),
        source='trip',          # يحول trip_id ↔︎ trip object
        write_only=True,
        required=False,
        allow_null=True,
    )

    customer_name = SerializerMethodField()

    class Meta:
        model  = Payment
        fields = [
            'id',
            'customer',
            'customer_name',
            'trip',       # يُعرَض كـ JSON كامل
            'trip_id',    # يُستقبَل في POST/PUT
            'fare',
            'new_balance',
            'timestamp',
            'payment_method',
        ]
        read_only_fields = ('timestamp',)  # (اشمعنا؟) لا يُسمح بتعديل الطابع الزمني

    def get_customer_name(self, obj):
        return obj.customer.name

# ============================
# Serializer for DeviceLocation
# ============================
class DeviceLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DeviceLocation
        fields = '__all__'
