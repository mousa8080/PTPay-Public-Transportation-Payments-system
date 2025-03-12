from rest_framework import serializers
from .models import Customer, Payment

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'  # تقدر تحدد الحقول مثل: ['id', 'name', 'uid', 'balance']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'  # تقدر تحدد الحقول مثل: ['id', 'customer', 'fare', 'new_balance', 'date', 'time']
