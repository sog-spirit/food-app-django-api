from .models import User
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
import jwt

def user_authentication(request):
    token = request.data['token']

    if not token:
        raise AuthenticationFailed('User is not authenticated')
    
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('JWT token expired')
    return payload

def user_permission_authentication(request):
    payload = user_authentication(request)
    user = User.objects.filter(id=payload['id']).first()
    if not user.is_staff or not user.is_superuser:
        raise AuthenticationFailed('Access denied')
    return payload