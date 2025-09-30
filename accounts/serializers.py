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
    total_drinks = serializers.SerializerMethodField()
    total_alcohol_ml = serializers.SerializerMethodField()
    xp_percentage = serializers.SerializerMethodField()
    xp_to_next_level = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "display_name",
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
            "total_alcohol_ml",
            "xp_percentage",
            "xp_to_next_level",
        ]
        read_only_fields = [
            "xp",
            "rank",
            "total_drinks",
            "total_alcohol_ml",
            "xp_percentage",
            "xp_to_next_level",
        ]

    def get_total_drinks(self, obj: Profile) -> int:
        return (
            obj.beer + obj.floco + obj.rum +
            obj.whiskey + obj.vodka + obj.tequila
        )

    def get_total_alcohol_ml(self, obj: Profile) -> int:
        return obj.calculate_alcohol_drank()

    def get_xp_percentage(self, obj: Profile) -> int:
        # model already exposes a property; mirror here so API is stable
        try:
            return int(obj.xp_percentage)
        except Exception:
            return 0

    def get_xp_to_next_level(self, obj: Profile):
        return obj.xp_to_next_level


# ---- Daily logs ----
class DailyLogSerializer(serializers.ModelSerializer):
    # allow partial payloads; default missing values to 0
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
                "beer", "floco", "rum", "whiskey", "vodka",
                "tequila", "shotguns", "snorkels", "thrown_up",
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
            "accepted",
            "created_at",
        ]
        read_only_fields = ["id", "from_user", "to_user", "accepted", "created_at"]

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    email = serializers.EmailField(required=False, allow_blank=True)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value