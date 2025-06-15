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
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
        "xp": profile.xp,
        "rank": profile.rank,
        "total_alcohol": profile.calculate_alcohol_drank()
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
        serializer.save(
            profile=self.request.user.profile,
            date=current_log_date()
        )
