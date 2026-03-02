import os
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class AppGateMiddleware(MiddlewareMixin):
    """
    Simple "private web" gate.
    - Requires ?k=<APP_GATE_KEY> on first visit (production)
    - Then stores gate state in session so users don't need the key every time
    - Skips API endpoints used by the Flutter app
    """

    SESSION_FLAG = "app_gate_ok"

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.expected_key = os.getenv("APP_GATE_KEY", "").strip()

    def process_request(self, request):
        # If no gate key is configured, do nothing
        if not self.expected_key:
            return None

        # In DEBUG, do nothing (so local dev is normal)
        if getattr(settings, "DEBUG", False):
            return None

        path = request.path or "/"

        # Always allow these paths (Flutter API + assets)
        if path.startswith("/accounts/api/"):
            return None
        if path.startswith("/static/"):
            return None
        if path.startswith("/media/"):
            return None

        # Optional: allow admin without gate (still protected by login)
        if path.startswith("/admin/"):
            return None

        # Allow Django health checks etc if you have them
        if path == "/favicon.ico":
            return None

        # If already unlocked this session, allow
        if request.session.get(self.SESSION_FLAG) is True:
            return None

        # Check key in querystring
        supplied = (request.GET.get("k") or "").strip()
        if supplied and supplied == self.expected_key:
            request.session[self.SESSION_FLAG] = True

            # Redirect to same URL WITHOUT the k param (clean URL)
            # Keep any other query params.
            q = request.GET.copy()
            if "k" in q:
                q.pop("k")

            new_url = path
            if q:
                new_url = f"{path}?{q.urlencode()}"

            return HttpResponseRedirect(new_url)

        # Not allowed: return a real 403 page (helps iOS safari views)
        return HttpResponseForbidden(
            "<html><head><meta name='viewport' content='width=device-width, initial-scale=1' />"
            "<title>Private</title></head>"
            "<body style='font-family:system-ui;background:#0f0c29;color:#fff;padding:24px;'>"
            "<h2 style='margin:0 0 8px;'>Private</h2>"
            "<p style='opacity:.8;margin:0 0 14px;'>This site isn’t publicly accessible.</p>"
            "<p style='opacity:.6;margin:0;'>If you’re the owner, open a link containing the access key.</p>"
            "</body></html>"
        )