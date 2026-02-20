from django.shortcuts import redirect
from django.urls import reverse

class PasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # allow logout and password change pages
            exempt_urls = [
                reverse('password_change'),
                reverse('logout'),
                reverse('admin:index'),
                reverse('admin:projects_user_change', args=[request.user.id]) if request.user.is_staff else None
            ]
            
            if not request.user.has_changed_password and request.path not in filter(None, exempt_urls):
                return redirect('password_change')

        response = self.get_response(request)
        return response
