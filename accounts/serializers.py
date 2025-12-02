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

# accounts/serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    display_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150
    )

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already taken."})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already in use."})
        return attrs

    def create(self, validated_data):
        # pull values
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password1']

        # 🔥 IMPORTANT: default display_name if missing/blank
        display_name = validated_data.get('display_name')
        if not display_name:
            display_name = username

        # create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # create profile with proper display_name
        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
        )

        return profile


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
