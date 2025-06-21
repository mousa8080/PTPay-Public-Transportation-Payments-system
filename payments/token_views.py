# File: payments/token_views.py

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer, Driver


class PassengerTokenSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")
        if not phone or not password:
            raise serializers.ValidationError("يجب إدخال رقم الهاتف وكلمة المرور")
        try:
            user = Customer.objects.get(phone=phone)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("رقم الهاتف أو كلمة المرور غير صحيحة")
        if not check_password(password, user.password):
            raise serializers.ValidationError("رقم الهاتف أو كلمة المرور غير صحيحة")
        if not user.is_active:
            raise serializers.ValidationError("الحساب غير مفعل")
        attrs['user'] = user
        return attrs


class PassengerTokenView(APIView):
    """
    POST /api/passenger/token/
    يبني أكسس+ريفريش توكن ويرجع uid
    """
    def post(self, request, *args, **kwargs):
        serializer = PassengerTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        access["uid"] = user.uid

        return Response({
            "refresh": str(refresh),
            "access": str(access),
            "uid":     user.uid
        }, status=status.HTTP_200_OK)


class DriverTokenSerializer(serializers.Serializer):
    phone          = serializers.CharField(required=True)
    password       = serializers.CharField(required=True, write_only=True)
    license_number = serializers.CharField(required=True)

    def validate(self, attrs):
        phone          = attrs.get("phone")
        password       = attrs.get("password")
        license_number = attrs.get("license_number")
        if not phone or not password or not license_number:
            raise serializers.ValidationError("يجب إدخال رقم الهاتف وكلمة المرور ورقم الرخصة")
        try:
            user = Driver.objects.get(phone=phone, license_number=license_number)
        except Driver.DoesNotExist:
            raise serializers.ValidationError("بيانات تسجيل الدخول غير صحيحة")
        if not check_password(password, user.password):
            raise serializers.ValidationError("بيانات تسجيل الدخول غير صحيحة")
        attrs['user'] = user
        return attrs


class DriverTokenView(APIView):
    """
    POST /api/driver/token/
    يبني أكسس+ريفريش توكن ويرجع بيانات السائق
    """
    def post(self, request, *args, **kwargs):
        serializer = DriverTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        access["driver_id"] = user.id

        wallet = user.wallet
        return Response({
            "refresh":         str(refresh),
            "access":          str(access),
            "driver_id":       user.id,
            "name":            user.name,
            "balance":         float(wallet.balance),
            "pending_balance": float(wallet.pending_balance),
        }, status=status.HTTP_200_OK)
