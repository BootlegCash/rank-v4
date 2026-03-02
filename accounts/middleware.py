from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse

class WebGateMiddleware:
    """
    Blocks public web access unless a valid gate key is provided.
    Allows Render health checks (HEAD /).
    Gate can be provided via:
      - header: X-AH-GATE: <key>
      - query param: ?k=<key>
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.gate_key = getattr(settings, "WEB_GATE_KEY", "")

        # Paths you want accessible (still gated unless you add them to "public")
        self.always_allow_paths = {
            "/favicon.ico",
        }

        # If you ever want certain pages PUBLIC (no key), add them here.
        # (You said you don't want the website accessible, so keep this empty.)
        self.public_paths = set()

    def __call__(self, request):
        # ✅ Allow Render health check (Render hits HEAD /)
        if request.method == "HEAD" and request.path == "/":
            return HttpResponse("ok")

        # Allow truly public paths (optional)
        if request.path in self.public_paths or request.path in self.always_allow_paths:
            return self.get_response(request)

        # If no gate key configured, don't block (safer for local dev)
        if not self.gate_key:
            return self.get_response(request)

        # Check header or query param
        header_key = request.META.get("HTTP_X_AH_GATE", "")
        query_key = request.GET.get("k", "")

        if header_key == self.gate_key or query_key == self.gate_key:
            return self.get_response(request)

        return HttpResponseForbidden("Forbidden")