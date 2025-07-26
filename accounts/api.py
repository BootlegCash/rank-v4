# accounts/api.py

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Profile, DailyLog
from .serializers import DailyLogSerializer
from datetime import date

# ✅ Utility function for today’s log date
def current_log_date():
    return date.today()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Return the current user's profile stats."""
    profile = request.user.profile
    return Response({
        "username": request.user.username,
        "email": request.user.email,
        "xp": profile.xp,
        "rank": profile.rank,
        "beer": profile.beer,
        "floco": profile.floco,
        "rum": profile.rum,
        "whiskey": profile.whiskey,
        "vodka": profile.vodka,
        "tequila": profile.tequila,
        "shotguns": profile.shotguns,
        "snorkels": profile.snorkels,
        "thrown_up": profile.thrown_up,
        "total_alcohol": profile.calculate_alcohol_drank(),
    })

class DailyLogViewSet(viewsets.ModelViewSet):
    """
    GET  /accounts/api/log_drink/         → list today's log
    POST /accounts/api/log_drink/         → create or update today's log
    """
    serializer_class = DailyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = current_log_date()
        return DailyLog.objects.filter(profile=self.request.user.profile, date=today)

    def perform_create(self, serializer):
        profile = self.request.user.profile
        today = current_log_date()

        # 🔧 Try to get or create today's log
        daily_log, created = DailyLog.objects.get_or_create(profile=profile, date=today)

        # Merge incoming data into existing daily log
        data = serializer.validated_data
        daily_log.beer += data.get('beer', 0)
        daily_log.floco += data.get('floco', 0)
        daily_log.rum += data.get('rum', 0)
        daily_log.whiskey += data.get('whiskey', 0)
        daily_log.vodka += data.get('vodka', 0)
        daily_log.tequila += data.get('tequila', 0)
        daily_log.shotguns += data.get('shotguns', 0)
        daily_log.snorkels += data.get('snorkels', 0)
        if data.get('thrown_up', False):
            daily_log.thrown_up += 1

        # Recalculate XP and save
        daily_log.xp = daily_log.calculate_xp()
        daily_log.save()

        # ✅ Update cumulative profile stats
        profile.beer += data.get('beer', 0)
        profile.floco += data.get('floco', 0)
        profile.rum += data.get('rum', 0)
        profile.whiskey += data.get('whiskey', 0)
        profile.vodka += data.get('vodka', 0)
        profile.tequila += data.get('tequila', 0)
        profile.shotguns += data.get('shotguns', 0)
        profile.snorkels += data.get('snorkels', 0)
        if data.get('thrown_up', False):
            profile.thrown_up += 1
        profile.save()

        print(f"✅ Updated daily log for {today}: beer={daily_log.beer}, xp={daily_log.xp}")
        print(f"✅ Updated profile totals: beer={profile.beer}, xp={profile.xp}")
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import Profile


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def register_api(request):
    """
    API endpoint to register a new user.
    Expects JSON with:
    username, email, password1, password2, display_name
    """
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password1 = request.data.get('password1', '')
    password2 = request.data.get('password2', '')
    display_name = request.data.get('display_name', '').strip()

    # ✅ basic validation
    if not username or not email or not password1 or not password2:
        return Response({'error': 'All fields are required.'}, status=400)

    if password1 != password2:
        return Response({'error': 'Passwords do not match.'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=400)

    # ✅ create user and profile
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password1
    )
    profile = Profile.objects.get(user=user)
    if display_name:
        profile.display_name = display_name
        profile.save()

    return Response({
        'success': True,
        'username': username,
        'email': email,
        'display_name': profile.display_name
    }, status=201)