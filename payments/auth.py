from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Driver

class DriverJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        driver_id = validated_token.get('driver_id')
        if not driver_id:
            raise AuthenticationFailed('driver_id missing in token', code='user_not_found')
        try:
            return Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            raise AuthenticationFailed('No such driver', code='user_not_found')
