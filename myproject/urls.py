from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static


def home(request):
    return HttpResponse("يا هلا والله")

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    # واجهات تطبيق المدفوعات
    path('api/', include('payments.urls')),
    # JWT refresh
    path('api/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#essa
