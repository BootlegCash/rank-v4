# myapp/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Main app routes
    path('api/', include('accounts.api_urls')),   # DRF API routes
    path('', RedirectView.as_view(url='/accounts/welcome/', permanent=False)),  # Default redirect
]
