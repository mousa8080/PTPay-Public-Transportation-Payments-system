from rest_framework import serializers
from .models import Customer, Payment

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'  # يمكنك تحديد الحقول المطلوبة مثل: ['id', 'name', 'uid', 'balance']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'customer', 'fare', 'new_balance', 'date', 'time', 'payment_method']
