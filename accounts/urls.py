from django.urls import path, include
from . import views
from .views import CreatePostView, profile_api, CreatePostView
from . import api
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api import (
    user_profile,
    DailyLogViewSet,
    friend_list_api,
    send_friend_request_api,
    accept_friend_request_api,
    reject_friend_request_api,
    remove_friend_api,
    search_users_api
)

router = DefaultRouter()
router.register(r'api/log_drink', DailyLogViewSet, basename='log_drink')

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('welcome/', views.welcome, name='welcome'),
    path('profile/', views.profile, name='profile'),
    path('update_stats/', views.update_stats, name='update_stats'),
    path('friend_list/', views.friend_list, name='friend_list'),
    path('friend_search/', views.friend_search, name='friend_search'),
    path('friend_profile/<str:username>/', views.friend_profile, name='friend_profile'),
    path('accept_friend_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject_friend_request/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('remove_friend/<int:profile_id>/', views.remove_friend, name='remove_friend'),
    path('send_friend_request/', views.send_friend_request, name='send_friend_request'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('posts/<int:post_id>/like/', views.like_post, name='like_post'),
    path('compose/', CreatePostView.as_view(), name='create_post'),
    path('safety/', views.safety_guidelines, name='safety_guidelines'),
    path('achievements/', views.achievements, name='achievements'),
    path('about/', views.about, name='about'),
    path('update_daily_log/', views.update_daily_log, name='update_daily_log'),
    path('daily_log_calendar/', views.daily_log_calendar, name='daily_log_calendar'),
    path('calendar/', views.monthly_calendar, name='monthly_calendar'),
    path('calendar/<int:year>/<int:month>/', views.monthly_calendar, name='monthly_calendar'),
    path('calendar/<int:year>/<int:month>/<int:day>/', views.day_log_detail, name='day_log_detail'),
    path('api/register/', api.register_api, name='register_api'),

    # ✅ API Endpoints for Friends and Profile
    path('api/profile/', user_profile, name='user_profile'),
    path('api/friends/', friend_list_api, name='friend_list_api'),
    path('api/friend/send/', send_friend_request_api, name='send_friend_request_api'),
    path('api/friend/accept/', accept_friend_request_api, name='accept_friend_request_api'),
    path('api/friend/reject/', reject_friend_request_api, name='reject_friend_request_api'),
    path('api/friend/remove/', remove_friend_api, name='remove_friend_api'),
    path('api/friend/search/', search_users_api, name='search_users_api'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),      # <-- add
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),     # <-- add
]

# DRF router URLs (for daily drink logging)
urlpatterns += router.urls
