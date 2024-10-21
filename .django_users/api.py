from django.contrib.auth import authenticate
from ninja import Router
from ninja.errors import AuthenticationError
from rest_framework.authtoken.models import Token

from users_module.schemas import EmailAndPasswordLoginSchema, TokenLoginSchema, UserSchema

router = Router()


@router.post("by-email", auth=None, response=UserSchema)
# def auth_by_email(request, email: str = Form(...), password: str = Form(...)):
def auth_by_email(request, payload: EmailAndPasswordLoginSchema):
    user = authenticate(username=payload.email, password=payload.password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return {
            "token": token.key,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "type": user.user_type,
        }
    raise AuthenticationError


@router.post("by-token", auth=None, response=UserSchema)
def auth_by_token(request, payload: TokenLoginSchema):
    try:
        token = Token.objects.get(key=payload.token)
        user = token.user
        return {
            "token": token.key,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "type": user.user_type,
        }
    except Token.DoesNotExist:
        raise AuthenticationError
