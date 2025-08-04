from rest_framework import serializers
from .models import DailyLog, Profile, FriendRequest
from django.contrib.auth.models import User

class DailyLogSerializer(serializers.ModelSerializer):
    beer = serializers.IntegerField(required=False, default=0)
    floco = serializers.IntegerField(required=False, default=0)
    rum = serializers.IntegerField(required=False, default=0)
    whiskey = serializers.IntegerField(required=False, default=0)
    vodka = serializers.IntegerField(required=False, default=0)
    tequila = serializers.IntegerField(required=False, default=0)
    shotguns = serializers.IntegerField(required=False, default=0)
    snorkels = serializers.IntegerField(required=False, default=0)
    thrown_up = serializers.IntegerField(required=False, default=0)
    xp = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyLog
        fields = [
            'date', 'beer', 'floco', 'rum', 'whiskey', 'vodka',
            'tequila', 'shotguns', 'snorkels', 'thrown_up', 'xp'
        ]
        read_only_fields = ['date', 'xp']


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    is_friend = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['id', 'username', 'display_name', 'xp', 'rank', 'is_friend']

    def get_is_friend(self, obj):
        request_user_profile = self.context['request'].user.profile
        return obj in request_user_profile.friends.all()


class FriendRequestSerializer(serializers.ModelSerializer):
    from_username = serializers.CharField(source='from_user.user.username', read_only=True)
    to_username = serializers.CharField(source='to_user.user.username', read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_username', 'to_username', 'accepted', 'created_at']
