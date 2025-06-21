# ===== File: payments/urls.py =====

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


from .views import (
    GovernorateListCreateAPIView,
    CityListCreateAPIView,
    CustomerListCreateAPIView,
    SingleCustomerAPIView,
    DriverListCreateAPIView,
    SingleDriverAPIView,
    VehicleListCreateAPIView,
    RouteListCreateAPIView,
    StartTripAPIView,
    DeviceLocationUpdateAPIView,
    ProcessPaymentAPIView,
    TransferAPIView,
    PaymentAPIView,
    CustomerListAPIViewOriginal,
    QrPaymentAPIViewOriginal,
    qr_uid_payment,
    CustomerWalletAPIView,
    DriverWalletAPIView,
    generate_trip_qr,
    EndTripAPIView,
    DriverActiveTripQRAPIView,
    ActiveTripAPIView,
    TripPaymentsListAPIView,
    PublicQRPageView,
    CustomerPaymentsAPIView,
    device_active_trip,
    update_balance,
    SingleDriverByUidAPIView,
    driver_make_payment,



)

from .token_views import PassengerTokenView, DriverTokenView

urlpatterns = [
    # إدارة المحافظ المنفصلة
    path('wallets/customers/', CustomerWalletAPIView.as_view(), name='customer-wallets'),
    path('wallets/drivers/',    DriverWalletAPIView.as_view(),   name='driver-wallets'),
    path('wallets/drivers/<int:driver_id>/', DriverWalletAPIView.as_view()),


    # Governorates & Cities
    path('governorates/', GovernorateListCreateAPIView.as_view(), name='governorate-list-create'),
    path('cities/',       CityListCreateAPIView.as_view(),       name='city-list-create'),

    # Passenger registration & login
    path('register/passenger/', CustomerListCreateAPIView.as_view(), name='register-passenger'),
    path('passenger/token/',    PassengerTokenView.as_view(),        name='passenger-token'),

    # Driver registration & login
    path('register/driver/', DriverListCreateAPIView.as_view(), name='register-driver'),
    path('driver/token/',    DriverTokenView.as_view(),         name='driver-token'),
    path('token/refresh/',   TokenRefreshView.as_view(),        name='token_refresh'),

    # Profiles
    path('customers/<str:uid>/', SingleCustomerAPIView.as_view(), name='single-customer'),
    path('driver/<int:id>/',      SingleDriverAPIView.as_view(),   name='single-driver'),

    # Vehicles & Routes
    path('vehicles/', VehicleListCreateAPIView.as_view(), name='vehicle-list-create'),
    path('routes/',   RouteListCreateAPIView.as_view(),   name='route-list-create'),

    # Trips
    path('trips/start/',      StartTripAPIView.as_view(),         name='start-trip'),
    path('trips/active/',     ActiveTripAPIView.as_view(),        name='active-trip'),
    path('trips/active/qr/',  DriverActiveTripQRAPIView.as_view(), name='driver-active-qr'),
    path('trips/<int:trip_id>/generate-qr/', generate_trip_qr,    name='generate-trip-qr'),
    path('trips/end/',        EndTripAPIView.as_view(),          name='end-trip'),
    path('payments/trip/',    TripPaymentsListAPIView.as_view(), name='trip-payments'),

    # Device location
    path('device/location/', DeviceLocationUpdateAPIView.as_view(), name='device-location'),

    # Payments & transfers
    path('payments/process/', ProcessPaymentAPIView.as_view(), name='process-payment'),
    path('transfers/',        TransferAPIView.as_view(),        name='transfer'),
    path('payments/',         PaymentAPIView.as_view(),         name='payment-original'),

    # Legacy & QR
    path('customers-list/', CustomerListAPIViewOriginal.as_view(), name='customer-list-original'),
    path('qr-payment/',      QrPaymentAPIViewOriginal.as_view(),   name='qr-payment-original'),
    path('qr-page/', PublicQRPageView.as_view(), name='qr-page'),
    path('qr-uid-payment/',  qr_uid_payment,                     name='qr-uid-payment'),
     # ... المسارات الموجودة
    path('customers/<str:uid>/payments/', CustomerPaymentsAPIView.as_view(), name='customer-payments'),

    path('device/active-trip/',device_active_trip,name='device-active-trip'),

    path('payments/update_balance/', update_balance, name='update-balance'),

    path('driver/uid/<str:uid>/', SingleDriverByUidAPIView.as_view(), name='driver-by-uid'),

    path('driver/pay/', driver_make_payment, name='driver-pay'),





]
