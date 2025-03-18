from django.urls import path
from .views import (
    PaymentAPIView, do_get, CustomerListAPIView,
    QrPaymentAPIView, qr_page, generate_qr_image, qr_uid_payment
)

urlpatterns = [
    path('do_get/', do_get, name='do_get'),
    path('api/payment/', PaymentAPIView.as_view(), name='payment_api'),
    path('api/customers/', CustomerListAPIView.as_view(), name='customer_list'),
    path('api/qr_payment/', QrPaymentAPIView.as_view(), name='qr_payment'),
    path('qr/', qr_page, name='qr_page'),
    path('qr_img/', generate_qr_image, name='generate_qr_image'),
    path('qr_uid/', qr_uid_payment, name='qr_uid_payment'),
]
