from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from .models import User

class ImpersonationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        impersonate_id = request.session.get('impersonate_user_id')
        if impersonate_id and request.user.is_authenticated and (request.user.role == 'professor' or request.user.is_staff):
            try:
                target_user = User.objects.get(id=impersonate_id)
                request.original_user = request.user
                request.user = target_user
                request.is_impersonating = True
            except User.DoesNotExist:
                del request.session['impersonate_user_id']
        else:
            request.is_impersonating = False

class PasswordChangeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.user.role == 'student':
            # Skip if professor is impersonating
            if getattr(request, 'is_impersonating', False):
                return None
                
            if not request.user.has_changed_password:
                # Allow access to password change views and logout
                allowed_paths = [
                    '/accounts/password_change/',
                    '/accounts/password_change/done/',
                    '/accounts/logout/',
                ]
                if request.path not in allowed_paths and not request.path.startswith('/static/'):
                    from django.shortcuts import redirect
                    return redirect('password_change')
