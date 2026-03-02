import os
from django.http import HttpResponseForbidden

class WebGateMiddleware:
    """
    Blocks normal browser traffic unless:
    - request includes X-APP-KEY header that matches APP_GATE_KEY
    OR
    - request is for admin/static/health etc. (allowlist)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.gate_key = os.getenv("APP_GATE_KEY", "")
        self.allow_prefixes = (
            "/static/",
            "/admin/",
            "/api/",          # allow your mobile API
        )

    def __call__(self, request):
        path = request.path

        # Allow certain paths always
        if path.startswith(self.allow_prefixes):
            return self.get_response(request)

        # If no gate key configured, do nothing
        if not self.gate_key:
            return self.get_response(request)

        # Allow if correct header present
        client_key = request.headers.get("X-APP-KEY", "")
        if client_key == self.gate_key:
            return self.get_response(request)

        # Otherwise block
        return HttpResponseForbidden("Web access disabled.")