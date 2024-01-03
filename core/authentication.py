from django.conf import settings
from rest_framework import status
import jwt
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import authentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from tracker.models import User
from django.core.exceptions import PermissionDenied

class JWTAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        auth_data = authentication.get_authorization_header(request)
        if not auth_data:
            return None
        
        prefix, token = auth_data.decode('utf-8').split(' ')

        try:
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
            try:
                user = User.objects.get(id=payload["user_id"])
            except:
                raise AuthenticationFailed('Invalid Token')
            return (user, token)
            
        except jwt.ExpiredSignatureError as e:
            raise NotAcceptable("Token has Expired")

        except jwt.exceptions.DecodeError as e:
            raise AuthenticationFailed('Invalid Token')