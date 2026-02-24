# accounts/urls.py
from django.urls import path, include
from . import views
from .views import CreatePostView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # HTML/session pages
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

    # API namespace for mobile
    path('api/', include('accounts.api_urls')),

    path('password_reset/', auth_views.PasswordResetView.as_view(
    template_name='accounts/password_reset_form.html',
    email_template_name='accounts/password_reset_email.txt',
    subject_template_name='accounts/password_reset_subject.txt',
), name='password_reset'),

path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
    template_name='accounts/password_reset_done.html'
), name='password_reset_done'),

path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
    template_name='accounts/password_reset_confirm.html'
), name='password_reset_confirm'),

path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
    template_name='accounts/password_reset_complete.html'
), name='password_reset_complete'),
]


