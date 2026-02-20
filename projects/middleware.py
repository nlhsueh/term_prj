from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from .models import User

class ImpersonationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        impersonate_id = request.session.get('impersonate_user_id')
        if impersonate_id and request.user.is_authenticated and (request.user.role == 'professor' or request.user.is_staff):
            try:
                target_user = User.objects.get(id=impersonate_id)
                # Store the original user so we can still check permissions if needed
                request.original_user = request.user
                # Override request.user for the duration of this request
                request.user = target_user
                request.is_impersonating = True
            except User.DoesNotExist:
                del request.session['impersonate_user_id']
        else:
            request.is_impersonating = False
