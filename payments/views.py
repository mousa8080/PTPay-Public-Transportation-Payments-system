# File: payments/views.py

import io
import json
import qrcode
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny



from .auth import DriverJWTAuthentication
from .models import (
    Governorate, City, Customer, Driver,
    Vehicle, Route, Trip, Payment,
    Device, DeviceLocation,
    CustomerWallet, DriverWallet, Transfer,
    Driver,
)
from .serializers import (
    GovernorateSerializer, CitySerializer,
    CustomerSerializer, DriverSerializer,
    VehicleSerializer, RouteSerializer,
    TripSerializer, PaymentSerializer,
    DeviceLocationSerializer,
    CustomerWalletSerializer, DriverWalletSerializer,
    TransferSerializer
)

# payments/views.py

from django.views import View
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse





# class UpdateBalanceAPIView(APIView):
#     def post(self, request):
#         uid        = request.data.get('uid','').strip()
#         new_balance = Decimal(request.data.get('new_balance','0.00'))
#         customer  = get_object_or_404(Customer, uid__iexact=uid)
#         wallet    = get_object_or_404(CustomerWallet, customer=customer)
#         wallet.balance = new_balance
#         wallet.save(update_fields=['balance'])
#         return Response({
#             "status":      "ok",
#             "new_balance": float(wallet.balance),
#         }, status=status.HTTP_200_OK)




class PublicQRPageView(View):
    """
    بيجيب driver_id من query param ويعرض صفحة QR.
    """
    def get(self, request):
        driver_id = request.GET.get('driver_id')
        if not driver_id:
            return HttpResponse('Missing driver_id', status=400)

        driver = get_object_or_404(Driver, id=driver_id)

        try:
            trip = Trip.objects.filter(
                driver=driver,
                end_time__isnull=True
            ).latest('start_time')
            context = {
                'trip_id':        trip.id,
                'vehicle_number': trip.vehicle.number
            }
        except Trip.DoesNotExist:
            # لا توجد رحلة حالية
            context = {'no_trip': True}

        return render(request, 'payments/qrcode.html', context)



class CustomerWalletAPIView(ListAPIView):
    serializer_class       = CustomerWalletSerializer
    permission_classes     = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        qs = CustomerWallet.objects.all()
        if cid := self.request.query_params.get('customer_id'):
            qs = qs.filter(customer_id=cid)
        return qs


class DriverWalletAPIView(ListAPIView):
    serializer_class       = DriverWalletSerializer
    permission_classes     = [IsAuthenticated]
    authentication_classes = [DriverJWTAuthentication]

    def get_queryset(self):
        qs = DriverWallet.objects.all()
        did = self.request.query_params.get('driver_id') or self.kwargs.get('driver_id')
        if did:
            qs = qs.filter(driver_id=did)
        return qs


class ActiveTripAPIView(APIView):
    authentication_classes = [DriverJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        driver = get_object_or_404(Driver, id=request.user.id)
        try:
            trip = Trip.objects.filter(
                driver=driver, end_time__isnull=True
            ).latest('start_time')
        except Trip.DoesNotExist:
            return Response({'error': 'No active trip.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TripSerializer(trip).data)


class TripPaymentsListAPIView(ListAPIView):
    serializer_class       = PaymentSerializer
    permission_classes     = [IsAuthenticated]
    authentication_classes = [DriverJWTAuthentication]

    def get_queryset(self):
        trip_id = self.request.query_params.get('trip_id')
        return Payment.objects.filter(trip_id=trip_id)


class GovernorateListCreateAPIView(ListCreateAPIView):
    queryset         = Governorate.objects.all()
    serializer_class = GovernorateSerializer


class CityListCreateAPIView(ListCreateAPIView):
    queryset         = City.objects.all()
    serializer_class = CitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if gov_id := self.request.query_params.get('governorate'):
            qs = qs.filter(governorate_id=gov_id)
        return qs


class CustomerListCreateAPIView(ListCreateAPIView):
    queryset         = Customer.objects.all()
    serializer_class = CustomerSerializer


class SingleCustomerAPIView(RetrieveAPIView):
    queryset         = Customer.objects.all()
    serializer_class = CustomerSerializer
    lookup_field     = 'uid'
    lookup_url_kwarg = 'uid'


class DriverListCreateAPIView(ListCreateAPIView):
    queryset         = Driver.objects.all()
    serializer_class = DriverSerializer


class SingleDriverAPIView(RetrieveAPIView):
    queryset         = Driver.objects.all()
    serializer_class = DriverSerializer
    lookup_field     = 'id'


class VehicleListCreateAPIView(ListCreateAPIView):
    queryset         = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class RouteListCreateAPIView(ListCreateAPIView):
    queryset         = Route.objects.all()
    serializer_class = RouteSerializer


class StartTripAPIView(APIView):
    authentication_classes = [DriverJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        driver  = request.user
        vehicle = get_object_or_404(Vehicle, id=request.data.get('vehicle_id'))
        route   = get_object_or_404(Route,   id=request.data.get('route_id'))

        # تأكد أن المركبة تخص السائق
        if vehicle.driver_id != driver.id:
            return Response({'error': 'This vehicle does not belong to you.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # تأكد أن للمسار نقاط توقف
        if not route.stops.exists():
            return Response({'error': 'المسار لا يحتوي على أية نقاط توقف (Stops).'},
                            status=status.HTTP_400_BAD_REQUEST)

        # حساب رقم التسلسل لليوم
        today = timezone.localdate()
        last  = Trip.objects.filter(driver=driver, date=today) \
                             .order_by('-sequence_number') \
                             .first()
        seq   = last.sequence_number + 1 if last else 1

        driver.in_zone = False
        driver.save(update_fields=['in_zone'])

        # إنشاء الرحلة بدون expected_passengers
        trip = Trip.objects.create(
            driver=driver,
            vehicle=vehicle,
            route=route,
            sequence_number=seq,
            start_time=timezone.now(),
            in_zone=False,
        )

        # ربط السائق بالمسار الجديد
        driver.assigned_route = route
        driver.save(update_fields=['assigned_route'])

        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)



@method_decorator(csrf_exempt, name='dispatch')
class DeviceLocationUpdateAPIView(APIView):
    def post(self, request):
        # 1) قراءة البيانات من الـ body
        try:
            data   = json.loads(request.body or '{}')
            device = get_object_or_404(Device, id=data.get('device_id'))
            lat    = float(data.get('latitude'))
            lng    = float(data.get('longitude'))
        except Exception:
            return JsonResponse({'error': 'Invalid data'}, status=400)

        # 2) حفظ الموقع
        loc = DeviceLocation.objects.create(
            device=device,
            latitude=lat,
            longitude=lng
        )

        # 3) جلب السائق والمسار المعيّن
        try:
            driver = device.driver
        except Driver.DoesNotExist:
            return JsonResponse({'error': 'Device not assigned'}, status=400)

        route = driver.assigned_route
        if not route:
            return JsonResponse({'error': 'No route assigned'}, status=400)

        # 4) تحقّق إذا دخل ضمن أي Stop
        stops = route.stops.all()
        in_zone = any(
            (stop.min_lat  <= lat <= stop.max_lat  and
             stop.min_lng  <= lng <= stop.max_lng)
            for stop in stops
        )

        # 5) حدّث حالة in_zone في صفّ السائق
        was_in = driver.in_zone
        driver.in_zone = in_zone
        driver.save(update_fields=['in_zone'])

        # 6) لو انتقل للتوّ من خارج المنطقة إلى داخلها
        if in_zone and not was_in:
            # أ) إنهاء الرحلة الحالية
            try:
                trip = (
                    Trip.objects
                    .filter(driver=driver, end_time__isnull=True)
                    .latest('start_time')
                )
                trip.end_time = timezone.now()
                trip.in_zone  = True
                trip.save(update_fields=['end_time', 'in_zone'])
            except Trip.DoesNotExist:
                pass

            # ب) نقل الـ pending_balance إلى balance
            try:
                dw = get_object_or_404(DriverWallet, driver=driver)
                dw.balance         += dw.pending_balance
                dw.pending_balance  = Decimal('0.00')
                dw.save(update_fields=['balance', 'pending_balance'])
            except DriverWallet.DoesNotExist:
                pass

            # ج) إلغاء ربط المسار عن السائق إذا أحببت
            # driver.assigned_route = None
            # driver.save(update_fields=['assigned_route'])

        # 7) أرسل الاستجابة
        return JsonResponse({
            'status':      'ok',
            'in_zone':     int(in_zone),
            'location_id': loc.id
        })



class ProcessPaymentAPIView(APIView):
    """
    POST /api/payments/process/
    Body JSON: {
      "uid": "<customer uid>",
      "trip_id": <trip id>,
      "fare": <decimal>,
      "payment_method": "nfc" or "qr" or ...
    }
    """
    def post(self, request):
        uid     = request.data.get('uid', '').strip()
        trip_id = request.data.get('trip_id')
        pm      = request.data.get('payment_method', 'unk').strip().lower()
        fare    = Decimal(request.data.get('fare', '0.00'))

        # 1) جلب الرحلة
        trip = get_object_or_404(Trip, id=trip_id)

        # 2) جلب العميل
        customer = get_object_or_404(Customer, uid__iexact=uid)

        # 3) منع السائق من الدفع لنفسه
        if trip.driver.uid and trip.driver.uid.strip().lower() == uid.lower():
            return Response({"error": "You cannot pay for your own trip."},
                            status=status.HTTP_403_FORBIDDEN)

        # 4) جلب محفظة العميل وفحص الرصيد
        customer_wallet = get_object_or_404(CustomerWallet, customer=customer)
        if customer_wallet.balance < fare:
            return Response({"error": "رصيد العميل غير كافٍ للدفع"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 5) حساب الرصيد الجديد وإنشاء سجل الدفع
        new_balance = customer_wallet.balance - fare
        serializer = PaymentSerializer(data={
            'customer':      customer.id,
            'trip_id':     trip.id,
            'fare':          fare,
            'new_balance':   new_balance,
            'payment_method': pm,
        })
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        # 6) خصم الرصيد من العميل
        customer_wallet.balance = new_balance
        customer_wallet.save(update_fields=['balance'])

        # 7) إضافة المبلغ إلى pending_balance للسائق
        dw = get_object_or_404(DriverWallet, driver=trip.driver)
        dw.pending_balance += fare
        dw.save(update_fields=['pending_balance'])

        # 8) إعادة البيانات للعميل
        return Response({
            "trip_id":     trip.id,
            "fare":        float(payment.fare),
            "new_balance": float(payment.new_balance),
            "timestamp":   payment.timestamp.isoformat(),
        }, status=status.HTTP_201_CREATED)



class TransferAPIView(APIView):
    def post(self, request):
        # استرجاع البيانات المطلوبة من الـ request
        from_phone = request.data.get('from_phone')
        to_phone = request.data.get('to_phone')
        amount = Decimal(request.data.get('amount', '0.00'))

        # تحقق من وجود المرسل والمستقبل
        sender = Customer.objects.filter(phone=from_phone).first() or Driver.objects.filter(phone=from_phone).first()
        receiver = Customer.objects.filter(phone=to_phone).first() or Driver.objects.filter(phone=to_phone).first()

        # إذا لم يتم العثور على المرسل أو المستقبل
        if not sender or not receiver:
            return Response({'error': 'العميل أو السائق غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        # التحقق من الرصيد
        if isinstance(sender, Customer):
            sender_wallet = get_object_or_404(CustomerWallet, customer=sender)
        else:
            sender_wallet = get_object_or_404(DriverWallet, driver=sender)

        if isinstance(receiver, Customer):
            receiver_wallet = get_object_or_404(CustomerWallet, customer=receiver)
        else:
            receiver_wallet = get_object_or_404(DriverWallet, driver=receiver)

        # التحقق من أن المرسل يمتلك رصيد كافٍ
        if sender_wallet.balance < amount:
            return Response({'error': 'رصيد المرسل غير كافٍ'}, status=status.HTTP_400_BAD_REQUEST)

        # خصم المبلغ من رصيد المرسل وإضافته إلى رصيد المستقبل
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount

        sender_wallet.save(update_fields=['balance'])
        receiver_wallet.save(update_fields=['balance'])

        # إنشاء سجل التحويل
        ct_sw = ContentType.objects.get_for_model(sender_wallet)
        ct_rw = ContentType.objects.get_for_model(receiver_wallet)

        transfer = Transfer.objects.create(
            sender_content_type=ct_sw,
            sender_object_id=sender_wallet.id,
            receiver_content_type=ct_rw,
            receiver_object_id=receiver_wallet.id,
            amount=amount
        )

        return Response(TransferSerializer(transfer).data, status=status.HTTP_201_CREATED)



class PaymentAPIView(APIView):
    def get(self, request, *args, **kwargs):
        qs = Customer.objects.all()
        return Response(CustomerSerializer(qs, many=True).data)
    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class CustomerListAPIViewOriginal(APIView):
    def get(self, request, *args, **kwargs):
        qs = Customer.objects.all()
        return Response(CustomerSerializer(qs, many=True).data)


class QrPaymentAPIViewOriginal(APIView):
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token','')
        if not token:
            return Response({"error":"Missing token"}, status=400)
        return Response({
            "message":"OK","client_name":"Test",
            "new_balance":45.0,"fare":5,"payment_method":"QR"
        })




@csrf_exempt
def qr_uid_payment(request):
    """
    POST /api/qr-uid-payment/
    body JSON: {
      "token": "<QR token>",
      "uid":   "<customer uid>",
      "fare":  <decimal>
    }
    """
    data  = json.loads(request.body or '{}')
    token = data.get('token')
    uid   = data.get('uid')
    fare  = Decimal(data.get('fare', '0.00'))

    if not token or not uid:
        return JsonResponse({"error": "Missing token or uid"}, status=400)

    # 1) جلب الرحلة عن طريق التوكن
    trip = get_object_or_404(Trip, qr_token=token)

    # 2) جلب العميل ومحفظته
    customer = get_object_or_404(Customer, uid__iexact=uid)
    wallet   = get_object_or_404(CustomerWallet, customer=customer)

    # 3) التحقق من الرصيد
    if wallet.balance < fare:
        return JsonResponse({"error": "رصيد العميل غير كافٍ"}, status=400)

    # 4) حساب الرصيد الجديد
    new_balance = wallet.balance - fare

    # 5) تسجيل الدفع مربوط بالرحلة
    Payment.objects.create(
        customer       = customer,
        trip           = trip,
        fare           = fare,
        new_balance    = new_balance,
        payment_method = 'qr'
    )

    # 6) تحديث رصيد العميل
    wallet.balance = new_balance
    wallet.save(update_fields=['balance'])

    # 7) إضافة الفارق إلى pending_balance لمحفظة السائق
    dw = get_object_or_404(DriverWallet, driver=trip.driver)
    dw.pending_balance += fare
    dw.save(update_fields=['pending_balance'])

    return JsonResponse({
        "status":      "ok",
        "new_balance": float(new_balance),
        "fare":        float(fare),
    }, status=200)


def generate_trip_qr(request, trip_id):
    """
    GET /api/trips/<trip_id>/generate-qr/
    تُرجع صورة QR (PNG) إذا كانت الرحلة ما تزال نشطة،
    وإلا تُرجع 410 Gone.
    """
    trip = get_object_or_404(Trip, id=trip_id)

    # ⭐ لا تولّد QR إذا كانت الرحلة منتهية
    if trip.end_time is not None:
        return HttpResponse('Trip has ended', status=410)  # 410 Gone

    token       = trip.get_qr_token()
    public_url  = getattr(settings, 'PUBLIC_URL', '')

    stops = list(trip.route.stops.order_by('id'))
    start = stops[0].name if stops else ''
    end   = stops[-1].name if stops else ''

    qr_data = (
        f"{public_url}/api/payments/process/"
        f"?token={token}"
        f"&trip_id={trip.id}"
        f"&from={start}"
        f"&to={end}"
        f"&dateTime={trip.start_time.isoformat()}"
        f"&vehicleNumber={trip.vehicle.number}"
    )

    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")

# payments/views.py  – EndTripAPIView (بعد التعديل)

class EndTripAPIView(APIView):
    authentication_classes = [DriverJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        driver = get_object_or_404(Driver, id=request.user.id)

        try:
            trip = (
                Trip.objects
                    .filter(driver=driver, end_time__isnull=True)
                    .latest('start_time')
            )
        except Trip.DoesNotExist:
            return Response(
                {'error': 'No active trip to end.'},
                status=status.HTTP_404_BAD_REQUEST
            )

        # ➤ أغلق الرحلة
        trip.end_time = timezone.now()
        trip.in_zone  = False     # لا نهتم بالموقع
        trip.save(update_fields=['end_time', 'in_zone'])

        # ➤ صفِّر in_zone في جدول السائق
        driver.in_zone = False
        driver.save(update_fields=['in_zone'])

        # ✅  حوِّل pending_balance إلى balance دائماً
        try:
            dw = DriverWallet.objects.get(driver=driver)
            dw.balance         += dw.pending_balance
            dw.pending_balance  = Decimal('0.00')
            dw.save(update_fields=['balance', 'pending_balance'])
        except DriverWallet.DoesNotExist:
            pass

        return Response(TripSerializer(trip).data)


class DriverActiveTripQRAPIView(APIView):
    """
    GET /api/driver/active-trip-qr/
    تُرجع صورة QR للرحلة النشطة الحالية للسائق (إذا وجدت).
    """
    authentication_classes = [DriverJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        driver = get_object_or_404(Driver, id=request.user.id)
        try:
            trip = Trip.objects.filter(
                driver=driver,
                end_time__isnull=True
            ).latest('start_time')
        except Trip.DoesNotExist:
            return Response(
                {'error': 'لا توجد رحلة نشطة حالياً.'},
                status=status.HTTP_404_NOT_FOUND
            )

        token      = trip.get_qr_token()
        public_url = getattr(settings, 'PUBLIC_URL', '')

        stops = list(trip.route.stops.order_by('id'))
        start = stops[0].name if stops else ''
        end   = stops[-1].name if stops else ''

        qr_data = (
            f"{public_url}/api/payments/process/"
            f"?token={token}"
            f"&trip_id={trip.id}"
            f"&from={start}"
            f"&to={end}"
        )

        img = qrcode.make(qr_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return HttpResponse(buf.getvalue(), content_type="image/png")



class CustomerPaymentsAPIView(ListAPIView):
    """
    ListAPIView لإرجاع جميع دفعات العميل بناءً على الـ uid
    GET /api/customers/<uid>/payments/
    """
    serializer_class = PaymentSerializer

    def get_queryset(self):
        uid = self.kwargs['uid']
        customer = get_object_or_404(Customer, uid=uid)
        # رتب النتائج حسب الأحدث أولاً
        return Payment.objects.filter(customer=customer).order_by('-timestamp')


from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def device_active_trip(request):
    """
    POST /api/device/active-trip/
    Body JSON: { "device_id": <int> }
    Response JSON:
      - { "active": true,  "trip_id": <int> }  إذا في رحلة شغالة
      - { "active": false }                    إذا مفيش رحلة
    """
    logger.debug("device_active_trip called with data: %r", request.data)

    device_id = request.data.get('device_id')
    if device_id is None:
        logger.debug("Missing device_id in request")
        return Response(
            {'active': False, 'error': 'MISSING_DEVICE_ID'},
            status=status.HTTP_200_OK
        )

    device = get_object_or_404(Device, id=device_id)
    logger.debug("Found Device id=%d → driver id=%d", device.id, device.driver.id)

    # ابحث عن أحدث رحلة لم تنتهِ بعد
    active_trip = (
        Trip.objects
            .filter(driver=device.driver, end_time__isnull=True)
            .order_by('-start_time')
            .first()
    )

    if active_trip:
        logger.debug("Active trip found: id=%d", active_trip.id)
        return Response(
            {'active': True, 'trip_id': active_trip.id},
            status=status.HTTP_200_OK
        )
    else:
        logger.debug("No active trip for device id=%d", device.id)
        return Response(
            {'active': False},
            status=status.HTTP_200_OK
        )








@api_view(['POST'])
@permission_classes([AllowAny])
def update_balance(request):
    uid       = request.data.get('uid', '').strip()
    new_bal   = Decimal(request.data.get('new_balance', '0.00'))
    action    = request.data.get('action', 'topup')
    device_id = request.data.get('device_id')  # لازم ترسل device_id

    # 1) جلب العميل ومحفظته
    customer = get_object_or_404(Customer, uid__iexact=uid)
    wallet   = get_object_or_404(CustomerWallet, customer=customer)

    if action == 'topup':
        # شحن الرصيد فقط
        wallet.balance = new_bal
        wallet.save(update_fields=['balance'])
        return Response({
            "status":      "recharged",
            "new_balance": float(wallet.balance)
        }, status=200)

    elif action == 'payment':
        # 2) احفظ الرصيد القديم وحسب المبلغ المدفوع
        old_balance = wallet.balance
        fare        = old_balance - new_bal

        # 3) خصم الرصيد
        wallet.balance = new_bal
        wallet.save(update_fields=['balance'])

        # 4) جلب الجهاز والسائق
        device = get_object_or_404(Device, id=device_id)
        driver = device.driver

        # 5) جلب الرحلة النشطة للسائق
        trip = (
            Trip.objects
                .filter(driver=driver, end_time__isnull=True)
                .latest('start_time')
        )

        # 6) إنشاء سجل الدفع
        Payment.objects.create(
            customer       = customer,
            trip           = trip,
            fare           = fare,
            new_balance    = new_bal,
            payment_method = 'nfc',
        )

        # 7) إضافة إلى pending_balance للسائق
        dw = get_object_or_404(DriverWallet, driver=driver)
        dw.pending_balance += fare
        dw.save(update_fields=['pending_balance'])

        return Response({
            "status":      "paid",
            "fare":        float(fare),
            "new_balance": float(wallet.balance)
        }, status=200)

    else:
        return Response({"error": "Invalid action"}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def driver_make_payment(request):
    uid = request.data.get('uid', '').strip()
    amount = Decimal(request.data.get('amount', '0.00'))

    # تحقق من السائق
    try:
        driver = Driver.objects.get(uid=uid)
    except Driver.DoesNotExist:
        return Response({"error": "Driver not found"}, status=404)

    # تحقق من وجود محفظة
    try:
        wallet = DriverWallet.objects.get(driver=driver)
    except DriverWallet.DoesNotExist:
        return Response({"error": "Driver wallet not found"}, status=404)

    # تحقق من الرصيد الكافي في balance فقط
    if wallet.balance < amount:
        return Response({"error": "Insufficient balance"}, status=400)

    # خصم المبلغ من الرصيد الفعلي
    wallet.balance -= amount
    wallet.save(update_fields=['balance'])

    return Response({
        "status": "ok",
        "new_balance": float(wallet.balance),
        "message": f"{amount} تم خصمه"
    }, status=200)

class SingleDriverByUidAPIView(APIView):
    """
    GET /api/driver/uid/<uid>/
    يرجع بيانات السائق بناءً على الـ uid
    """
    permission_classes = [AllowAny]  # أو IsAuthenticated إذا تبي محدد
    def get(self, request, uid, *args, **kwargs):
        driver = get_object_or_404(Driver, uid=uid)
        serializer = DriverSerializer(driver)
        return Response(serializer.data)



class QREnterUIDView(View):
    """
    GET /qr-enter-uid/?trip_id=...
    يعرض النموذج لإدخال الـ UID ثم يرسله لـ API
    """
    def get(self, request):
        trip_id = request.GET.get('trip_id')
        return render(request, 'payments/qr_enter_uid.html', {
            'trip_id': trip_id,
            # إذا كنت تمرّر قيمة fare ديناميكياً، أضفها هنا أيضاً:
            'fare': 7,
        })