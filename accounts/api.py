# accounts/api.py
from rest_framework import viewsets, permissions
from .models import DailyLog, current_log_date
from .serializers import DailyLogSerializer

class DailyLogViewSet(viewsets.ModelViewSet):
    """
    GET  /api/log_drink/         → list today's log
    POST /api/log_drink/         → update (or create) today's log
    """
    serializer_class = DailyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # only the current day's log for this user
        today = current_log_date()
        return DailyLog.objects.filter(profile=self.request.user.profile, date=today)

    def perform_create(self, serializer):
        # attach the profile and date automatically
        serializer.save(
            profile=self.request.user.profile,
            date=current_log_date()
        )