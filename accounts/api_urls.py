# accounts/api_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api as v


urlpatterns = [
    # Auth (JWT)
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Me
    path("profile/", v.me, name="api_me"),

    # Friends (unchanged)
    path("friends/", v.friends_list, name="api_friends_list"),
    path("friends/requests/", v.requests_list, name="api_requests_list"),
    path("friends/search/", v.user_search, name="api_user_search"),
    path("friends/request/send/", v.send_request, name="api_send_request"),
    path("friends/request/<int:request_id>/accept/", v.accept_request, name="api_accept_request"),
    path("friends/request/<int:request_id>/reject/", v.reject_request, name="api_reject_request"),
    path("friends/remove/", v.remove_friend, name="api_remove_friend"),
    path('register/', v.register, name='api_register'),

    # Log drink (NEW)
    path("log_drink/", v.log_drink, name="api_log_drink"),


    path('leaderboard/', v.leaderboard, name='api_leaderboard'),

    path('feed/', v.feed, name='api_feed'),
    path('feed/create/', v.create_post, name='api_create_post'),
    path('posts/<int:post_id>/like/', v.like_post_api, name='api_like_post'),
    
     # 🔥 FRIEND PUBLIC PROFILE (THIS IS WHAT FEED/FRIENDS CLICK USE)
    path(
        "friends/<str:username>/",
        v.friend_profile_api,
        name="friend-profile-api",
    ),

  path('calendar/', v.monthly_calendar_api, name='api_monthly_calendar'),
path('calendar/<int:year>/<int:month>/', v.monthly_calendar_api, name='api_monthly_calendar_ym'),
path('calendar/<int:year>/<int:month>/<int:day>/', v.day_log_detail_api, name='api_day_log_detail'),
path('rank-history/', v.rank_history, name='api_rank_history'),

    # Tokens
    path('tokens/', v.token_balance, name='api_token_balance'),
    path('tokens/earn/', v.earn_tokens, name='api_earn_tokens'),
    path('tokens/spend/', v.spend_tokens_api, name='api_spend_tokens'),
    path('tokens/history/', v.token_history, name='api_token_history'),
]
