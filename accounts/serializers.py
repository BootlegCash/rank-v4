# accounts/serializers.py

from rest_framework import serializers
from .models import DailyLog

class DailyLogSerializer(serializers.ModelSerializer):
    beer = serializers.IntegerField(required=False, default=0)
    floco = serializers.IntegerField(required=False, default=0)
    rum = serializers.IntegerField(required=False, default=0)
    whiskey = serializers.IntegerField(required=False, default=0)
    vodka = serializers.IntegerField(required=False, default=0)
    tequila = serializers.IntegerField(required=False, default=0)
    shotguns = serializers.IntegerField(required=False, default=0)
    snorkels = serializers.IntegerField(required=False, default=0)
    thrown_up = serializers.BooleanField(required=False, default=False)
    xp = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyLog
        fields = [
            'date',
            'beer',
            'floco',
            'rum',
            'whiskey',
            'vodka',
            'tequila',
            'shotguns',
            'snorkels',
            'thrown_up',
            'xp'
        ]
        read_only_fields = ['date', 'xp']
