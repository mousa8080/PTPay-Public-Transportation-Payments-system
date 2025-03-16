# payments/urls.py
from django.urls import path
from .views import PaymentAPIView, do_get

urlpatterns = [
    path('do_get/', do_get, name='do_get'),  # الطريقة القديمة
    path('api/payment/', PaymentAPIView.as_view(), name='payment_api'),  # API لـ Flutter
]
