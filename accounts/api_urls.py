# accounts/api_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api as v

urlpatterns = [
    # Auth (JWT)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Me
    path('me/', v.me, name='api_me'),

    # Friends
    path('friends/', v.friends_list, name='api_friends_list'),
    path('friends/requests/', v.requests_list, name='api_requests_list'),
    path('friends/search/', v.user_search, name='api_user_search'),
    path('friends/request/send/', v.send_request, name='api_send_request'),
    path('friends/request/<int:request_id>/accept/', v.accept_request, name='api_accept_request'),
    path('friends/request/<int:request_id>/reject/', v.reject_request, name='api_reject_request'),
    path('friends/remove/', v.remove_friend, name='api_remove_friend'),
]
