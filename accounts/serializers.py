# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, DailyLog, FriendRequest


# ------------------ Mini helpers ------------------

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


# ------------------ Main profile (admin/internal) ------------------

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
        read_only_fields = ["xp", "rank", "total_drinks"]


# ------------------ Public/mobile profile core shape ------------------

class ProfilePublicSerializer(serializers.Serializer):
    """
    Stable shape the mobile app can rely on.
    Extra counters can be added by the API function after validating this core.
    """
    username = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField()
    avatar_url = serializers.URLField()
    rank = serializers.CharField()
    xp = serializers.IntegerField()
    next_rank_xp = serializers.IntegerField()


# ------------------ Daily logs ------------------

class DailyLogSerializer(serializers.ModelSerializer):
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
                "beer", "floco", "rum", "whiskey", "vodka", "tequila",
                "shotguns", "snorkels", "thrown_up",
            } and v is not None and v < 0:
                raise serializers.ValidationError({k: "Must be >= 0"})
        return attrs


# ------------------ Friends ------------------

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = ProfileMiniSerializer(read_only=True)
    to_user = ProfileMiniSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ["id", "from_user", "to_user", "status", "created_at"]
        read_only_fields = ["id", "from_user", "to_user", "created_at"]


# ------------------ Mobile: log-drink request/response ------------------

class LogDrinkRequestSerializer(serializers.Serializer):
    """
    Accepts EITHER:
      A) Detailed: drink_name + abv_percent + volume_oz [+ count]
      B) Shortcut: category in {beer, floco, rum, whiskey, vodka, tequila} [+ count]
    """
    # Option A (detailed)
    drink_name  = serializers.CharField(required=False, allow_blank=True)
    abv_percent = serializers.FloatField(required=False, min_value=0.01)
    volume_oz   = serializers.FloatField(required=False, min_value=0.1)

    # Option B (shortcut)
    category = serializers.ChoiceField(
        choices=["beer", "floco", "rum", "whiskey", "vodka", "tequila"],
        required=False
    )

    count    = serializers.IntegerField(required=False, default=1, min_value=1)
    shotguns = serializers.IntegerField(required=False, default=0, min_value=0)
    snorkels = serializers.IntegerField(required=False, default=0, min_value=0)
    notes    = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        have_category = bool(data.get("category"))
        have_detail = all(k in data and data[k] not in (None, "")
                          for k in ("drink_name", "abv_percent", "volume_oz"))
        if not (have_category or have_detail):
            raise serializers.ValidationError(
                "Provide either {category, count} OR "
                "{drink_name, abv_percent, volume_oz[, count]}."
            )
        return data


class LogDrinkComputedSerializer(serializers.Serializer):
    std_drinks_per_item = serializers.FloatField()
    total_std_drinks = serializers.FloatField()


class LogDrinkResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    message = serializers.CharField()
    drink_name = serializers.CharField(allow_blank=True)
    abv_percent = serializers.FloatField(required=False)
    volume_oz = serializers.FloatField(required=False)
    category = serializers.CharField(required=False)
    count = serializers.IntegerField()
    shotguns = serializers.IntegerField()
    snorkels = serializers.IntegerField()
    notes = serializers.CharField(allow_blank=True)
    computed = LogDrinkComputedSerializer()
