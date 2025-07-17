from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts endpoints
    path('accounts/', include('accounts.urls')),

    # ✅ Mount API endpoints at /accounts/api/
    path('accounts/api/', include('accounts.api_urls')),
]
