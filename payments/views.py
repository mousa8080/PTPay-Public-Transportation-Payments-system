# views.py

import json
from decimal import Decimal
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Customer, Payment

# ----------------------------
# Legacy Function-Based View (do_get)
# ----------------------------
@csrf_exempt
def do_get(request):
    if request.method != 'POST':
        return HttpResponse("Method Not Allowed", status=405)
    
    try:
        data = json.loads(request.body)
        uid = data.get('uid', '').strip()
    except Exception as e:
        return HttpResponse("Invalid JSON", status=400)
    
    if not uid:
        return HttpResponse("Missing_UID", content_type="text/plain")
    
    try:
        customer = Customer.objects.get(uid=uid)
    except Customer.DoesNotExist:
        return HttpResponse("Not_Registered", content_type="text/plain")
    
    fare = Decimal('5')
    new_balance = customer.balance - fare
    if new_balance < 0:
        return HttpResponse("Insufficient_Balance", content_type="text/plain")
    
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
        time=time_str
    )
    
    return HttpResponse("OK", content_type="text/plain")


# -------------------------------------
# New DRF-based API View (using APIView)
# -------------------------------------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class PaymentAPIView(APIView):
    """
    API لمعالجة عملية الدفع باستخدام Django REST Framework.
    يستقبل POST ببيانات JSON (مع مفتاح 'uid')، ويتعامل مع العميل والدفع.
    """
    def post(self, request, *args, **kwargs):
        uid = request.data.get('uid', '').strip()
        if not uid:
            return Response({"error": "Missing UID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(uid=uid)
        except Customer.DoesNotExist:
            return Response({"error": "Not Registered"}, status=status.HTTP_404_NOT_FOUND)

        fare = Decimal('5')
        new_balance = customer.balance - fare
        if new_balance < 0:
            return Response({"error": "Insufficient Balance"}, status=status.HTTP_400_BAD_REQUEST)

        customer.balance = new_balance
        customer.save()

        now = timezone.localtime()
        date_str = now.strftime('%d/%m/%Y')
        time_str = now.strftime('%H:%M:%S')

        payment = Payment.objects.create(
            customer=customer,
            fare=fare,
            new_balance=new_balance,
            date=date_str,
            time=time_str
        )

        return Response({"message": "OK", "payment_id": payment.id}, status=status.HTTP_200_OK)
