from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [

    path('', accounts_views.welcome, name='home'),
    path('admin/', admin.site.urls),

    # Accounts endpoints
    path('accounts/', include('accounts.urls')),

    # ✅ Mount API endpoints at /accounts/api/
    path('accounts/api/', include('accounts.api_urls')),
]
