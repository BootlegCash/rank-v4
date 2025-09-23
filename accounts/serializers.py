# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, DailyLog, FriendRequest

# ---- Mini helpers ----

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ProfileMiniSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "display_name",
            "rank",
            "xp",
        ]


# ---- Main profile (internal / admin-ish) ----
class ProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "display_name",
            "bio",
            "xp",
            "rank",
            "beer",
            "floco",
            "rum",
            "whiskey",
            "vodka",
            "tequila",
            "shotguns",
            "snorkels",
            "thrown_up",
            "total_drinks",
        ]
        read_only_fields = [
            "xp",
            "rank",
            "total_drinks",
        ]


# ---- Public/mobile profile payload ----
class ProfilePublicSerializer(serializers.Serializer):
    """
    What Flutter consumes. We keep this decoupled from the DB model so the app’s
    response stays stable even if models change.
    """
    username = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField()
    avatar_url = serializers.URLField()
    rank = serializers.CharField()
    xp = serializers.IntegerField()
    next_rank_xp = serializers.IntegerField()


# ---- Daily logs ----
class DailyLogSerializer(serializers.ModelSerializer):
    # Make all drink counts optional with default 0 so partial posts don't explode
    beer = serializers.IntegerField(required=False, default=0, min_value=0)
    floco = serializers.IntegerField(required=False, default=0, min_value=0)
    rum = serializers.IntegerField(required=False, default=0, min_value=0)
    whiskey = serializers.IntegerField(required=False, default=0, min_value=0)
    vodka = serializers.IntegerField(required=False, default=0, min_value=0)
    tequila = serializers.IntegerField(required=False, default=0, min_value=0)
    shotguns = serializers.IntegerField(required=False, default=0, min_value=0)
    snorkels = serializers.IntegerField(required=False, default=0, min_value=0)
    thrown_up = serializers.IntegerField(required=False, default=0, min_value=0)

    xp = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyLog
        fields = [
            "id",
            "date",
            "beer",
            "floco",
            "rum",
            "whiskey",
            "vodka",
            "tequila",
            "shotguns",
            "snorkels",
            "thrown_up",
            "xp",
        ]

    def validate(self, attrs):
        for k, v in attrs.items():
            if k in {
                "beer",
                "floco",
                "rum",
                "whiskey",
                "vodka",
                "tequila",
                "shotguns",
                "snorkels",
                "thrown_up",
            } and v is not None and v < 0:
                raise serializers.ValidationError({k: "Must be >= 0"})
        return attrs


# ---- Friend requests ----
class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = ProfileMiniSerializer(read_only=True)
    to_user = ProfileMiniSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = [
            "id",
            "from_user",
            "to_user",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "from_user", "to_user", "created_at"]


# ---- Log drink request/response (mobile endpoint) ----
class LogDrinkRequestSerializer(serializers.Serializer):
    drink_name = serializers.CharField()
    abv_percent = serializers.FloatField(min_value=0.01)
    volume_oz = serializers.FloatField(min_value=0.1)
    count = serializers.IntegerField(min_value=1, default=1)
    shotguns = serializers.IntegerField(min_value=0, default=0)
    snorkels = serializers.IntegerField(min_value=0, default=0)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

class LogDrinkComputedSerializer(serializers.Serializer):
    std_drinks_per_item = serializers.FloatField()
    total_std_drinks = serializers.FloatField()

class LogDrinkResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    message = serializers.CharField()
    drink_name = serializers.CharField()
    abv_percent = serializers.FloatField()
    volume_oz = serializers.FloatField()
    count = serializers.IntegerField()
    shotguns = serializers.IntegerField()
    snorkels = serializers.IntegerField()
    notes = serializers.CharField(allow_blank=True)
    computed = LogDrinkComputedSerializer()
    # log_id = serializers.IntegerField(required=False)
