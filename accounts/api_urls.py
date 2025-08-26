# accounts/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .api import (
    DailyLogViewSet,
    user_profile,
    send_friend_request_api,
    accept_friend_request_api,
    reject_friend_request_api,
    remove_friend_api,
    friend_list_api,
)

router = DefaultRouter()
router.register(r'log_drink', DailyLogViewSet, basename='log-drink')

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('profile/', user_profile, name='api_profile'),

    # Friends
    path('friends/', friend_list_api, name='api_friend_list'),
    path('friends/send/', send_friend_request_api, name='api_send_friend_request'),
    path('friends/accept/<int:request_id>/', accept_friend_request_api, name='api_accept_friend_request'),
    path('friends/reject/<int:request_id>/', reject_friend_request_api, name='api_reject_friend_request'),
    path('friends/remove/<int:profile_id>/', remove_friend_api, name='api_remove_friend'),
    
    # Include DRF router URLs
    path('', include(router.urls)),
]
