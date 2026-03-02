import os
from django.http import HttpResponseForbidden

class AppGateMiddleware:
    """
    Simple "app-only" gate for HTML pages.
    - Accepts gate key via:
        1) query param ?k=...
        2) header X-App-Gate-Key: ...
    - If valid once, stores session flag so redirects still work.
    - Always allows API + static + admin assets.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Prefer APP_GATE_KEY, but accept WEB_GATE_KEY / web_gate_key too
        self.expected_key = (
            os.getenv("APP_GATE_KEY")
            or os.getenv("WEB_GATE_KEY")
            or os.getenv("web_gate_key")
        )

    def __call__(self, request):
        # If no key configured, don't gate anything
        if not self.expected_key:
            return self.get_response(request)

        path = request.path or "/"

        # Always allow these (otherwise your app + admin assets break)
        if (
            path.startswith("/static/")
            or path.startswith("/media/")
            or path.startswith("/accounts/api/")  # Flutter hits this
            or path == "/favicon.ico"
        ):
            return self.get_response(request)

        # Render health checks often do HEAD /
        # If you block this, Render can think your service is unhealthy.
        ua = (request.META.get("HTTP_USER_AGENT") or "")
        if request.method == "HEAD" and path == "/":
            return self.get_response(request)
        if "Go-http-client" in ua and path == "/":
            return self.get_response(request)

        # If already unlocked in this session, allow
        if request.session.get("app_gate_ok") is True:
            return self.get_response(request)

        # Check key from querystring or header
        provided = request.GET.get("k") or request.headers.get("X-App-Gate-Key")

        if provided and provided == self.expected_key:
            request.session["app_gate_ok"] = True
            response = self.get_response(request)

            # Also drop a cookie (helps some browser cases)
            response.set_cookie(
                "app_gate_ok",
                "1",
                max_age=60 * 60 * 24 * 7,  # 7 days
                secure=True,
                httponly=True,
                samesite="Lax",
            )
            return response

        # Cookie fallback (if session got cleared but cookie exists)
        if request.COOKIES.get("app_gate_ok") == "1":
            request.session["app_gate_ok"] = True
            return self.get_response(request)

        return HttpResponseForbidden("Forbidden: app gate key required.")