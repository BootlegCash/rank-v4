# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, DailyLog, FriendRequest, Post

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
    status = serializers.SerializerMethodField()

    class Meta:
        model = FriendRequest
        fields = ["id", "from_user", "to_user", "status", "accepted", "created_at"]
        read_only_fields = fields

    def get_status(self, obj):
        return "accepted" if getattr(obj, "accepted", False) else "pending"

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    # keep DRF happy but we'll fill this from aliases if missing
    password = serializers.CharField(write_only=True, min_length=6, max_length=128, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    # optional confirmation field (we’ll also look for aliases)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate(self, attrs):
        # Pull password from any alias the client might send
        data = {**getattr(self, "initial_data", {}), **attrs}
        pw = (
            data.get("password")
            or data.get("pass")
            or data.get("pwd")
            or data.get("password1")
        )
        cpw = (
            data.get("confirm_password")
            or data.get("password2")
            or data.get("confirmPassword")
        )

        if not pw:
            raise serializers.ValidationError({"password": "This field is required."})
        if len(pw) < 6:
            raise serializers.ValidationError({"password": "Must be at least 6 characters."})
        # If a confirmation was provided, make sure it matches
        if cpw is not None and cpw != "" and pw != cpw:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Write back unified fields so the view can read them
        attrs["password"] = pw
        attrs["confirm_password"] = cpw or ""
        return attrs
class PostSerializer(serializers.ModelSerializer):
    user = ProfileMiniSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",         # ProfileMiniSerializer
            "content",
            "created_at",
            "like_count",
            "is_liked",
        ]

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not hasattr(request, "user") or not request.user.is_authenticated:
            return False
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return False
        return obj.likes.filter(id=profile.id).exists()
