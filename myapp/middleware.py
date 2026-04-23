from django.http import HttpResponseForbidden

ALLOWED_PATHS = [
    '/accounts/api/',
    '/admin/',
    '/accounts/api/',
    '/admin/',
    '/accounts/password_reset/',
    '/accounts/reset/',         # password_reset_confirm links look like /accounts/reset/uidb64/token/
    '/accounts/password_reset_done/',
    '/accounts/password_reset_complete/',
    '/static/',  
]

class StaffOnlyWebMiddleware:
    """
    Blocks all non-API web routes from public access.
    Only staff/superusers can access web-facing views.
    API routes and admin are whitelisted.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Always allow API routes and admin through
        for allowed in ALLOWED_PATHS:
            if path.startswith(allowed):
                return self.get_response(request)

        # Allow logged-in staff through (for your browser testing)
        if request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)

        # Block everyone else
        return HttpResponseForbidden("Not available.")