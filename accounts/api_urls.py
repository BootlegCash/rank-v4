# accounts/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import DailyLogViewSet  # Make sure this exists and imports correctly

router = DefaultRouter()
router.register(r'log_drink', DailyLogViewSet, basename='log-drink')

urlpatterns = [
    path('', include(router.urls)),
]
