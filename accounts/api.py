# accounts/api.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Profile, DailyLog
from django.contrib.auth.models import User
from .serializers import DailyLogSerializer

from datetime import date

# Utility function to get today's log date
def current_log_date():
    return date.today()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
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
    GET  /api/log_drink/         → list today's log
    POST /api/log_drink/         → update (or create) today's log
    """
    serializer_class = DailyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = current_log_date()
        return DailyLog.objects.filter(profile=self.request.user.profile, date=today)

    def perform_create(self, serializer):
        profile = self.request.user.profile
        today = current_log_date()

        # Save log
        log = serializer.save(profile=profile, date=today)

        # Debug: Log incoming data
        print("🧾 Drink Log Data:", serializer.validated_data)

        # Update profile totals
        profile.beer += log.beer
        profile.floco += log.floco
        profile.rum += log.rum
        profile.whiskey += log.whiskey
        profile.vodka += log.vodka
        profile.tequila += log.tequila
        profile.shotguns += log.shotguns
        profile.snorkels += log.snorkels
        if log.thrown_up:
            profile.thrown_up += 1
        profile.xp += log.xp

        profile.save()

        print(f"✅ Updated profile: beer={profile.beer}, xp={profile.xp}")
