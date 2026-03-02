import os
from django.http import HttpResponseForbidden, HttpResponse


class WebGateMiddleware:
    """
    Protects the web UI from public access.

    - Allows API routes for Flutter
    - Allows password reset pages
    - Allows Render health checks
    - Blocks everything else unless correct gate key is provided

    Gate key can be passed via:
        ?gate=<key>
        Header: X-AH-GATE: <key>
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.gate_key = os.getenv("APP_GATE_KEY", "")

        # Routes that should ALWAYS be accessible
        self.allowed_prefixes = (
            "/accounts/api/",            # Flutter API
            "/accounts/password_reset/",
            "/accounts/reset/",          # password confirm links
            "/accounts/password_reset/done/",
            "/accounts/reset/done/",
            "/static/",
            "/media/",
            "/favicon.ico",
        )

    def __call__(self, request):
        path = request.path

        # ✅ Allow Render health check (HEAD /)
        if request.method == "HEAD" and path == "/":
            return HttpResponse("ok")

        # ✅ Always allow specific prefixes
        for prefix in self.allowed_prefixes:
            if path.startswith(prefix):
                return self.get_response(request)

        # ✅ If no gate key set, don't block (safe for local dev)
        if not self.gate_key:
            return self.get_response(request)

        # Check for gate key in query param or header
        query_key = request.GET.get("gate", "")
        header_key = request.META.get("HTTP_X_AH_GATE", "")

        if query_key == self.gate_key or header_key == self.gate_key:
            return self.get_response(request)

        # ❌ Block everything else
        return HttpResponseForbidden("Forbidden")