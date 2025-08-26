# accounts/serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import DailyLog, Profile, FriendRequest


# ---------- Helpers / small serializers ----------
class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


# ---------- Daily Log ----------
class DailyLogSerializer(serializers.ModelSerializer):
    # allow partial updates by making fields optional with defaults
    beer      = serializers.IntegerField(required=False, default=0, min_value=0)
    floco     = serializers.IntegerField(required=False, default=0, min_value=0)
    rum       = serializers.IntegerField(required=False, default=0, min_value=0)
    whiskey   = serializers.IntegerField(required=False, default=0, min_value=0)
    vodka     = serializers.IntegerField(required=False, default=0, min_value=0)
    tequila   = serializers.IntegerField(required=False, default=0, min_value=0)
    shotguns  = serializers.IntegerField(required=False, default=0, min_value=0)
    snorkels  = serializers.IntegerField(required=False, default=0, min_value=0)
    thrown_up = serializers.IntegerField(required=False, default=0, min_value=0)

    # server-calculated
    xp = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyLog
        fields = [
            "date",
            "beer", "floco", "rum", "whiskey", "vodka", "tequila",
            "shotguns", "snorkels", "thrown_up",
            "xp",
        ]
        read_only_fields = ["date", "xp"]


# ---------- Profile (used for /accounts/api/profile/ and friends lists) ----------
class ProfileSerializer(serializers.ModelSerializer):
    username        = serializers.CharField(source="user.username", read_only=True)
    display_name    = serializers.SerializerMethodField()
    is_friend       = serializers.SerializerMethodField()
    xp_percentage   = serializers.SerializerMethodField()
    xp_to_next_rank = serializers.SerializerMethodField()
    total_alc_ml    = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "id",
            "username",
            "display_name",
            "rank",
            "xp",
            "xp_percentage",
            "xp_to_next_rank",
            # drink/stat fields
            "beer", "floco", "rum", "whiskey", "vodka", "tequila",
            "shotguns", "snorkels", "thrown_up",
            "total_alc_ml",
            # social
            "is_friend",
        ]

    # ---- computed fields ----
    def get_display_name(self, obj):
        # fall back to username if not set
        val = getattr(obj, "display_name", None)
        return val if val else obj.user.username

    def get_is_friend(self, obj):
        # guarded access in case serializer context has no request
        req = self.context.get("request")
        if not req or not getattr(req, "user", None) or not req.user.is_authenticated:
            return False
        try:
            me = req.user.profile
        except Exception:
            return False
        return obj in me.friends.all()

    def get_xp_percentage(self, obj):
        # your template uses profile.xp_percentage property; keep same value if present
        try:
            return int(getattr(obj, "xp_percentage"))
        except Exception:
            # simple fallback if property not defined
            return 0

    def get_xp_to_next_rank(self, obj):
        # mirrors template usage xp_to_next_level/xp_to_next_rank
        # try both attribute names to be resilient
        if hasattr(obj, "xp_to_next_level"):
            return getattr(obj, "xp_to_next_level")
        return getattr(obj, "xp_to_next_rank", 0)

    def get_total_alc_ml(self, obj):
        # keep aligned with profile.calculate_alcohol_drank used in templates
        try:
            return int(obj.calculate_alcohol_drank())
        except Exception:
            return 0


# ---------- Friend Request ----------
class FriendRequestSerializer(serializers.ModelSerializer):
    from_username = serializers.CharField(source="from_user.user.username", read_only=True)
    to_username   = serializers.CharField(source="to_user.user.username", read_only=True)

    class Meta:
        model = FriendRequest
        fields = ["id", "from_username", "to_username", "accepted", "created_at"]
