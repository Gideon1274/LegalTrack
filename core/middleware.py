from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


class SessionTimeoutMiddleware:
    """Auto-logout after 10 minutes of inactivity (Module 1)."""

    TIMEOUT_SECONDS = 60 * 10

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        safe_prefixes = (
            reverse('login'),
            reverse('logout'),
            reverse('password_reset'),
            '/accounts/reset/',
            '/accounts/activate/',
            '/admin/',
            '/static/',
        )

        if user and user.is_authenticated and not request.path.startswith(safe_prefixes):
            last = request.session.get('last_activity')
            now_ts = int(timezone.now().timestamp())

            if last is not None and (now_ts - int(last)) > self.TIMEOUT_SECONDS:
                logout(request)
                request.session.flush()
                messages.info(request, 'You have been logged out due to inactivity.')
                return redirect('login')

            request.session['last_activity'] = now_ts

        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    """Redirect users to set a new password if they are flagged for first-login reset."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and getattr(user, 'must_change_password', False):
            set_password_path = reverse('set_password')
            safe_prefixes = (
                set_password_path,
                reverse('logout'),
                reverse('login'),
                '/admin/',
                '/static/',
            )
            if not request.path.startswith(safe_prefixes):
                return redirect('set_password')

        return self.get_response(request)
