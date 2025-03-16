# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("يا هلا والله")

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('payments/', include('payments.urls')),  # توجيه الطلبات لتطبيق payments
]
