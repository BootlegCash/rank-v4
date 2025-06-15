# myapp/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Redirect root to welcome
    path('', RedirectView.as_view(pattern_name='welcome', permanent=False)),

    # App URLs
    path('accounts/', include('accounts.urls')),
    path('competitions/', include('competitions.urls')),

    # DRF API routes (token auth, log drink, profile info)
    path('api/', include('accounts.api_urls')),  # this should include token, log_drink, profile endpoints
]
