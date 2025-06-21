# File: payments/token_serializers.py

from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import AccessToken
from .models import Customer, Driver


class PassengerTokenSerializer(serializers.Serializer):
    """
    Serializer للتحقق من phone/password للراكب وإنشاء JWT + uid.
    """
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

        # إصدار توكن باستخدام SimpleJWT
        token = AccessToken.for_user(user)
        # إضافة uid في الـpayload إن احتجت
        token["uid"] = user.uid

        return {"access": str(token)}


class DriverTokenSerializer(serializers.Serializer):
    """
    Serializer للتحقق من phone/password/license_number للسائق وإنشاء JWT.
    """
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

        # إصدار توكن باستخدام SimpleJWT
        token = AccessToken.for_user(user)
        # إضافة driver_id في الـpayload ليُعاد للـclient إذا احتاج
        token["driver_id"] = user.id

        return {"access": str(token)}
