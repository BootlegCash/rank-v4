# accounts/serializers.py
from rest_framework import serializers
from .models import DailyLog

class DailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLog
        fields = [
            'date', 'profile', 'beer', 'floco', 'rum', 'whiskey',
            'vodka', 'tequila', 'shotguns', 'snorkels', 'thrown_up', 'xp'
        ]
        read_only_fields = ['date', 'profile', 'xp']
