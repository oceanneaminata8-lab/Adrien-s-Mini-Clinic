from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import AuthToken


class ExpiringTokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].decode().lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed('Invalid authorization header.')

        try:
            raw_key = header[1].decode()
            token = AuthToken.objects.select_related('user').get(key_hash=AuthToken.digest(raw_key))
        except (UnicodeError, AuthToken.DoesNotExist):
            raise exceptions.AuthenticationFailed('Invalid or expired session.')

        if token.expires_at <= timezone.now() or not token.user.is_active:
            token.delete()
            raise exceptions.AuthenticationFailed('Invalid or expired session.')

        token.last_used_at = timezone.now()
        token.save(update_fields=['last_used_at'])
        return token.user, token
