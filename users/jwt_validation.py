from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from .models import CmEmployees
from django.utils import timezone

class EmployeeJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_header(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()
        if len(auth) != 2:
            return None
        return auth

    def get_raw_token(self, header):
        auth_type, raw_token = header
        if auth_type.lower() != 'bearer':
            return None
        return raw_token

    def get_validated_token(self, raw_token):
        try:
            return UntypedToken(raw_token)
        except TokenError as e:
            raise InvalidToken(e.args[0])

    def get_user(self, validated_token):
        try:
            employee_id = validated_token['employee_id']
            employee = CmEmployees.objects.get(id=employee_id)

            # Get the token's last login time
            token_last_login_time = validated_token.get('last_login_time', None)

            # Compare with employee's last_login_time
            if not employee.last_login_time or token_last_login_time != employee.last_login_time.timestamp():
                raise InvalidToken('Token has been invalidated due to a new login session.')

            return employee
        except KeyError:
            raise InvalidToken('Token contained no recognizable employee identification')
        except CmEmployees.DoesNotExist:
            raise InvalidToken('No employee matching this token was found')
