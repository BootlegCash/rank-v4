# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, DailyLog, FriendRequest

# ---- Mini helpers ----

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


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


# ---- Main profile ----

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
            # per-drink aggregates kept on Profile (if your model has them)
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
        # Additional guard just in case
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

    def create(self, validated_data):
        """
        Let your model/business logic compute xp and update Profile totals
        in model save() or a post_save signal. If you already do that, cool —
        this just passes data through.
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


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
