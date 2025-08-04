from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from rest_framework.authtoken import views as drf_views

urlpatterns = [

    path('', accounts_views.welcome, name='home'),
    path('admin/', admin.site.urls),

    # Accounts endpoints
    path('accounts/', include('accounts.urls')),

    # ✅ Mount API endpoints at /accounts/api/
    path('accounts/api/', include('accounts.api_urls')),

    path('api/token/', drf_views.obtain_auth_token, name='api_token_auth'),
]
