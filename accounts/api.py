# accounts/api.py
from rest_framework import viewsets, permissions

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Profile
from django.contrib.auth.models import User
from .serializers import DailyLogSerializer
from .models import DailyLog

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
    serializer_class = DailyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = current_log_date()
        return DailyLog.objects.filter(profile=self.request.user.profile, date=today)

    def create(self, request, *args, **kwargs):
        data = request.data
        profile = request.user.profile
        date = current_log_date()

        # Get or create the DailyLog for today
        log, created = DailyLog.objects.get_or_create(profile=profile, date=date)

        # Update fields based on incoming data
        fields = ['beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila', 'shotguns', 'snorkels', 'thrown_up']
        for field in fields:
            if field in data:
                try:
                    value = int(data[field])
                    setattr(log, field, getattr(log, field, 0) + value)
                except (ValueError, TypeError):
                    return Response(
                        {'error': f'Invalid value for {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Recalculate XP
        log.xp = log.calculate_xp()
        log.save()

        serializer = self.get_serializer(log)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
