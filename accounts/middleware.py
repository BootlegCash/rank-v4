import os
from django.http import HttpResponse, HttpResponseForbidden


class WebGateMiddleware:
    """
    App-gated web UI.

    Always allow:
      - Flutter API routes
      - Password reset flow routes
      - static/media
      - Render health checks

    Gate key can be passed via:
      - ?k=<key> or ?gate=<key>
      - Header: X-AH-GATE: <key>
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.gate_key = os.getenv("APP_GATE_KEY", "").strip()

        self.always_allow_prefixes = (
            "/accounts/api/",

            # Password reset flow:
            "/accounts/password_reset/",
            "/accounts/reset/",              # includes /accounts/reset/<uid>/<token>/ and /set-password/
            "/accounts/password_reset/done/",
            "/accounts/reset/done/",

            # Static:
            "/static/",
            "/media/",
            "/favicon.ico",
        )

    def _has_valid_key(self, request) -> bool:
        if not self.gate_key:
            return True  # dev-safe: no key means no gating

        q_k = (request.GET.get("k", "") or "").strip()
        q_gate = (request.GET.get("gate", "") or "").strip()
        h_key = (request.headers.get("X-AH-GATE", "") or "").strip()

        return (q_k == self.gate_key) or (q_gate == self.gate_key) or (h_key == self.gate_key)

    def __call__(self, request):
        path = request.path

        # ✅ Render health checks
        if request.method in ("HEAD",) and path == "/":
            return HttpResponse("ok")

        # ✅ Always allow these
        for prefix in self.always_allow_prefixes:
            if path.startswith(prefix):
                return self.get_response(request)

        # ✅ Homepage: return a harmless 200 page (prevents iOS “network lost” UX)
        if path == "/":
            return HttpResponse(
                """
                <!doctype html>
                <html>
                <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
                <body style="font-family: -apple-system, system-ui; padding: 24px;">
                  <h2>After Hours: Ranked</h2>
                  <p>This service is app-only.</p>
                </body>
                </html>
                """,
                content_type="text/html",
                status=200,
            )

        # ✅ Gate check for everything else
        if self._has_valid_key(request):
            return self.get_response(request)

        return HttpResponseForbidden("Forbidden")