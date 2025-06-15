# accounts/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import DailyLogViewSet, user_profile
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'log_drink', DailyLogViewSet, basename='log-drink')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', user_profile, name='api_profile'),
]
