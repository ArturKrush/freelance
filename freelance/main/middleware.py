from django.utils.deprecation import MiddlewareMixin
from .utils import change_database_credentials

class DynamicDBConnectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.session.get('authenticated_user')
        if user:
            # Можна зберігати пароль у сесії (або іншій безпечній формі)
            password = request.session.get('user_password')
            if password:
                change_database_credentials(user, password)