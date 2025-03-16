import json
import logging
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Customer, Payment

# إعداد نظام تسجيل الأخطاء
logger = logging.getLogger(__name__)

# ----------------------------
# Legacy Function-Based View (do_get) - (يفضل استخدام DRF بدلاً منه)
# ----------------------------
@csrf_exempt
def do_get(request):
    if request.method != 'POST':
        return HttpResponse("Method Not Allowed", status=405)

    try:
        data = json.loads(request.body)
        uid = data.get('uid', '').strip()
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)

    if not uid:
        return HttpResponse("Missing_UID", content_type="text/plain")

    customer = Customer.objects.filter(uid=uid).first()
    if not customer:
        return HttpResponse("Not_Registered", content_type="text/plain")

    fare = Decimal('5')
    if customer.balance < fare:
        return HttpResponse("Insufficient_Balance", content_type="text/plain")

    customer.balance -= fare
    customer.save()

    now = timezone.localtime()
    Payment.objects.create(
        customer=customer,
        fare=fare,
        new_balance=customer.balance,
        date=now.strftime('%d/%m/%Y'),
        time=now.strftime('%H:%M:%S')
    )

    return HttpResponse("OK", content_type="text/plain")

# -------------------------------------
# New DRF-based API View (using APIView)
# -------------------------------------
class PaymentAPIView(APIView):
    """
    API لمعالجة عمليات الدفع باستخدام Django REST Framework.
    يتلقى طلب `POST` يحتوي على `uid` ويتعامل مع الدفع وتحديث الرصيد.
    """

    def post(self, request, *args, **kwargs):
        uid = request.data.get('uid', '').strip()
        
        if not uid:
            return Response({"error": "Missing UID"}, status=status.HTTP_400_BAD_REQUEST)

        # البحث عن العميل أو إرجاع 404
        customer = get_object_or_404(Customer, uid=uid)

        fare = Decimal('5')
        if customer.balance < fare:
            return Response({"error": "Insufficient Balance"}, status=status.HTTP_400_BAD_REQUEST)

        # تحديث الرصيد
        customer.balance -= fare
        customer.save()

        now = timezone.localtime()

        # تسجيل المعاملة
        payment = Payment.objects.create(
            customer=customer,
            fare=fare,
            new_balance=customer.balance,
            date=now.strftime('%d/%m/%Y'),
            time=now.strftime('%H:%M:%S')
        )

        return Response({"message": "OK", "payment_id": payment.id}, status=status.HTTP_200_OK)
