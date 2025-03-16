import io
import qrcode
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.crypto import get_random_string
from decimal import Decimal
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Customer, Payment
from .serializers import CustomerSerializer

@method_decorator(csrf_exempt, name='dispatch')
class PaymentAPIView(APIView):
    """
    API لمعالجة عملية الدفع باستخدام Django REST Framework.
    يستقبل طلب POST ببيانات JSON تحتوي على 'uid' و(اختياريًا) 'payment_method'.
    تُرجع الاستجابة بالشكل التالي في حالات مختلفة:
    
    1. عند النجاح:
       {
         "message": "OK",
         "client_name": "<اسم العميل>",
         "new_balance": <الرصيد الجديد>,
         "fare": 5,
         "date": "<تاريخ العملية>",
         "time": "<وقت العملية>",
         "payment_method": "<NFC Card or QR>",
         "status": "Successful"
       }
    
    2. عند عدم كفاية الرصيد:
       {
         "message": "Not Successful (No balance)",
         "client_name": "<اسم العميل>",
         "current_balance": <الرصيد الحالي>,
         "fare": 5,
         "status": "Failed"
       }
    
    3. عند عدم تسجيل العميل:
       {
         "message": "Not Successful (Card not registered)",
         "status": "Failed"
       }
    """
    def post(self, request, *args, **kwargs):
        uid = request.data.get('uid', '').strip()
        if not uid:
            return Response({"error": "Missing UID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(uid=uid)
        except Customer.DoesNotExist:
            return Response({
                "message": "Not Successful (Card not registered)",
                "status": "Failed"
            }, status=status.HTTP_404_NOT_FOUND)
        
        fare = Decimal('5')
        new_balance = customer.balance - fare
        if new_balance < 0:
            return Response({
                "message": "Not Successful (No balance)",
                "client_name": customer.name,
                "current_balance": float(customer.balance),
                "fare": 5,
                "status": "Failed"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # قراءة payment_method من الطلب، وفي حال عدم وجوده نستخدم القيمة الافتراضية 'qr'
        payment_method = request.data.get('payment_method', 'qr').strip().lower()
        # تحديث رصيد العميل وإتمام العملية
        customer.balance = new_balance
        customer.save()
        
        now = timezone.localtime()
        date_str = now.strftime('%d/%m/%Y')
        time_str = now.strftime('%H:%M:%S')
        
        Payment.objects.create(
            customer=customer,
            fare=fare,
            new_balance=new_balance,
            date=date_str,
            time=time_str,
            payment_method=payment_method
        )
        
        # تحويل قيمة طريقة الدفع إلى الصيغة المرغوبة في الاستجابة
        display_payment_method = "NFC Card" if payment_method == "nfc" else "QR"
        
        return Response({
            "message": "OK",
            "client_name": customer.name,
            "new_balance": float(new_balance),
            "fare": 5,
            "date": date_str,
            "time": time_str,
            "payment_method": display_payment_method,
            "status": "Successful"
        }, status=status.HTTP_200_OK)

@csrf_exempt
def do_get(request):
    if request.method != 'POST':
        return Response("Method Not Allowed", status=status.HTTP_405_METHOD_NOT_ALLOWED)
    return Response({"error": "Legacy do_get not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)

class CustomerListAPIView(APIView):
    """
    API لاسترجاع قائمة بجميع العملاء المسجلين.
    تُرجع الاستجابة قائمة بالعملاء باستخدام الـ CustomerSerializer.
    """
    def get(self, request, *args, **kwargs):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class QrPaymentAPIView(APIView):
    """
    API لمعالجة الدفع عبر QR Code.
    يستقبل طلب GET مع معلمة 'token' في URL.
    هنا مثال توضيحي بسيط.
    """
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token', '')
        if not token:
            return Response({"error": "Missing token"}, status=status.HTTP_400_BAD_REQUEST)
        # منطق الدفع عبر QR يمكن تطويره لاحقاً؛ هنا نُرجع استجابة ثابتة
        return Response({
            "message": "OK",
            "client_name": "Test Client",
            "new_balance": 45.0,
            "fare": 5
        }, status=status.HTTP_200_OK)

def qr_page(request):
    """
    View لعرض صفحة الويب التي تحتوي على رمز QR.
    يتم استخدام قالب (template) qrcode.html الموجود في payments/templates/payments/.
    """
    return render(request, 'payments/qrcode.html')

@csrf_exempt
def qr_uid_payment(request):
    """
    View لمعالجة عملية الدفع عبر QR Code باستخدام إدخال UID يدويًا.
    يجب أن يكون هناك معلمة 'token' في URL (أي يتم الوصول إليها بعد مسح رمز QR).
    إذا لم يكن هناك token، يتم إظهار رسالة تفيد بضرورة مسح رمز QR أولاً.
    """
    token = request.GET.get('token', '')
    if not token:
        return HttpResponse("Please scan the QR code first.", content_type="text/plain")
    
    context = {'token': token}
    if request.method == 'POST':
        uid = request.POST.get('uid', '').strip()
        if not uid:
            context['error'] = "Please enter your UID."
        else:
            try:
                customer = Customer.objects.get(uid=uid)
            except Customer.DoesNotExist:
                context['error'] = "Not Successful (Card not registered)"
                return render(request, 'payments/qr_uid_payment.html', context)
            
            fare = Decimal('5')
            new_balance = customer.balance - fare
            if new_balance < 0:
                context['error'] = "Not Successful (No balance)"
                context['client_name'] = customer.name
                context['current_balance'] = float(customer.balance)
                return render(request, 'payments/qr_uid_payment.html', context)
            
            # إجراء عملية الدفع عبر QR، مع تحديد طريقة الدفع كـ "qr"
            customer.balance = new_balance
            customer.save()
            now = timezone.localtime()
            date_str = now.strftime('%d/%m/%Y')
            time_str = now.strftime('%H:%M:%S')
            Payment.objects.create(
                customer=customer,
                fare=fare,
                new_balance=new_balance,
                date=date_str,
                time=time_str,
                payment_method="qr"
            )
            context['success'] = "Payment successful!"
            context['client_name'] = customer.name
            context['new_balance'] = float(new_balance)
    return render(request, 'payments/qr_uid_payment.html', context)

def generate_qr_image(request):
    """
    View لتوليد صورة QR.
    يتم توليد token فريد وتضمين رابط الدفع عبر QR باستخدام صفحة إدخال UID.
    يُرجع صورة QR بصيغة PNG.
    """
    token = get_random_string(20)
    public_url = "https://1fe8-156-197-64-193.ngrok-free.app"
    # نوجه الرابط لصفحة إدخال UID
    qr_data = public_url + "/payments/qr_uid/?token=" + token
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_stream = buf.getvalue()
    return HttpResponse(image_stream, content_type="image/png")
