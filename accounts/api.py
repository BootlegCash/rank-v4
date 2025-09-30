# accounts/api.py
from datetime import datetime

from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import RegisterSerializer  # <-- add this
from .models import Profile, FriendRequest, DailyLog, current_log_date
from django.templatetags.static import static
from .serializers import (
    ProfileMiniSerializer,
    ProfileSerializer,
    FriendRequestSerializer,
    DailyLogSerializer,
)



# -------- Helpers --------
def _me(request) -> Profile:
    return request.user.profile


def _safe_int(val, default=0):
    try:
        if val is None or val == "":
            return default
        return int(val)
    except (TypeError, ValueError):
        return default


def _abs(request, relurl: str) -> str:
    return request.build_absolute_uri(relurl)

def _static_abs(request, relpath: str) -> str:
    return _abs(request, static(relpath))

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    profile = user.profile

    # Display name: prefer profile.display_name, fallback to first_name, then username
    display_name = (getattr(profile, "display_name", "") or "").strip() \
                   or (getattr(user, "first_name", "") or "").strip() \
                   or user.username

    # Avatar (fallback to static placeholder)
    avatar_url = None
    if getattr(profile, "avatar", None):
        try:
            avatar_url = _abs(request, profile.avatar.url)
        except Exception:
            pass
    if not avatar_url:
        avatar_url = _static_abs(request, "img/avatar_placeholder.png")

    # Counters
    beer     = int(getattr(profile, "beer", 0) or 0)
    floco    = int(getattr(profile, "floco", 0) or 0)
    rum      = int(getattr(profile, "rum", 0) or 0)
    whiskey  = int(getattr(profile, "whiskey", 0) or 0)
    vodka    = int(getattr(profile, "vodka", 0) or 0)
    tequila  = int(getattr(profile, "tequila", 0) or 0)
    computed_total = beer + floco + rum + whiskey + vodka + tequila

    shotguns  = int(getattr(profile, "shotguns", 0) or 0)
    snorkels  = int(getattr(profile, "snorkels", 0) or 0)
    thrown_up = int(getattr(profile, "thrown_up", 0) or 0)

    # Rank/XP
    rank_name    = getattr(profile, "rank", "Bronze")
    xp           = int(getattr(profile, "xp", 0) or 0)
    next_rank_xp = int(getattr(profile, "next_rank_xp", 600) or 600)

    resp = {
        "username": user.username,
        "email": user.email or "",
        "display_name": display_name,
        "avatar_url": avatar_url,
        "rank": rank_name,
        "xp": xp,
        "next_rank_xp": next_rank_xp,

        "beer": beer, "floco": floco, "rum": rum,
        "whiskey": whiskey, "vodka": vodka, "tequila": tequila,

        # plural aliases some UIs use
        "beers": beer, "flocos": floco, "rums": rum,
        "whiskeys": whiskey, "vodkas": vodka, "tequilas": tequila,

        # totals + aliases
        "total_drinks": computed_total,
        "total": computed_total,
        "totalDrinks": computed_total,

        "shotguns": shotguns,
        "snorkels": snorkels,
        "thrown_up": thrown_up,
    }
    return Response(resp, status=status.HTTP_200_OK)


# -------- Friends: lists --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def friends_list(request):
    me = _me(request)
    friends = me.friends.all().order_by("user__username")
    return Response(ProfileMiniSerializer(friends, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def requests_list(request):
    me = _me(request)
    received = FriendRequest.objects.filter(to_user=me, accepted=False).order_by("-created_at")
    sent     = FriendRequest.objects.filter(from_user=me, accepted=False).order_by("-created_at")
    return Response({
        "received": FriendRequestSerializer(received, many=True).data,
        "sent":     FriendRequestSerializer(sent, many=True).data,
    })


# -------- Friends: search / send / accept / reject / remove --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_search(request):
    """
    Search users by username.
    ?q=partial  → up to 10 profiles (not you, not already friends).
    """
    q = (request.GET.get("q") or "").strip()
    me = _me(request)
    if not q:
        return Response([], status=200)
    qs = Profile.objects.filter(user__username__icontains=q).exclude(id=me.id)[:10]
    # exclude already-friends
    qs = [p for p in qs if p not in me.friends.all()]
    return Response(ProfileMiniSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def send_request(request):
    """JSON: { "username": "target" }"""
    me = _me(request)
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)

    try:
        to = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    if to == me:
        return Response({"detail": "cannot send request to yourself"}, status=400)
    if to in me.friends.all():
        return Response({"detail": "already friends"}, status=409)
    if FriendRequest.objects.filter(from_user=me, to_user=to, accepted=False).exists():
        return Response({"detail": "request already sent"}, status=409)
    if FriendRequest.objects.filter(from_user=to, to_user=me, accepted=False).exists():
        return Response({"detail": "they already sent you a request"}, status=409)

    fr = FriendRequest.objects.create(from_user=me, to_user=to)  # pending
    return Response(FriendRequestSerializer(fr).data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def accept_request(request, request_id: int):
    me = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=me, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.accept()  # establishes mutual friendship
    return Response({"detail": "friend request accepted"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reject_request(request, request_id: int):
    me = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=me, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.delete()
    return Response({"detail": "friend request rejected"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def remove_friend(request):
    """JSON: { "username": "target" }  – removes both directions."""
    me = _me(request)
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)
    try:
        other = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    if other not in me.friends.all():
        return Response({"detail": "not friends"}, status=409)

    me.friends.remove(other)
    other.friends.remove(me)
    return Response({"detail": "removed from friends"}, status=200)


# -------- Drinks logging --------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def log_drink(request):
    """
    Upserts to today's DailyLog AND rolls increments into Profile totals.

    Accepts partial payload, all fields optional:
    {
      "date": "YYYY-MM-DD" (optional; defaults to current_log_date()),
      "beer": 1, "floco": 0, "rum": 0, "whiskey": 0, "vodka": 0, "tequila": 0,
      "shotguns": 0, "snorkels": 0, "thrown_up": 0
    }
    """
    me = _me(request)

    # Determine log date
    raw_date = (request.data.get("date") or "").strip()
    if raw_date:
        try:
            log_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "date must be YYYY-MM-DD"}, status=400)
    else:
        log_date = current_log_date()

    # Extract increments (default 0)
    fields = [
        "beer", "floco", "rum", "whiskey", "vodka", "tequila",
        "shotguns", "snorkels", "thrown_up",
    ]
    inc = {f: _safe_int(request.data.get(f), 0) for f in fields}
    # Short-circuit if nothing to change
    if not any(inc.values()):
        return Response({"detail": "No changes supplied."}, status=400)

    # Guard negative values
    for k, v in inc.items():
        if v < 0:
            return Response({k: "Must be >= 0"}, status=400)

    # Get/create the daily log, add increments
    daily_log, _ = DailyLog.objects.get_or_create(profile=me, date=log_date)
    for f, add in inc.items():
        setattr(daily_log, f, getattr(daily_log, f, 0) + add)
    daily_log.xp = daily_log.calculate_xp()
    daily_log.save()

    # ALSO roll into the lifetime Profile totals
    for f, add in inc.items():
        if hasattr(me, f):
            setattr(me, f, getattr(me, f, 0) + add)
    me.save()  # triggers XP & rank recompute in Profile.save()

    return Response(
        {
            "profile": ProfileSerializer(me).data,
            "daily_log": DailyLogSerializer(daily_log).data,
            "detail": "Logged successfully.",
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def register(request):
    """
    POST /accounts/api/register/
    Accepts password aliases (password, pass, pwd, password1) and confirmation
    aliases (confirm_password, password2, confirmPassword).
    """
    ser = RegisterSerializer(data=request.data)
    if not ser.is_valid():
        return Response({"detail": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    data = ser.validated_data

    username = data["username"].strip()
    password = data["password"]             # unified by serializer
    email = (data.get("email") or "").strip()
    display_name = (data.get("display_name") or "").strip() or username

    # Create user & profile
    user = User.objects.create_user(username=username, password=password, email=email)
    profile = getattr(user, "profile", None)
    if profile is None:
        profile = Profile.objects.create(user=user, display_name=display_name)
    elif not getattr(profile, "display_name", ""):
        profile.display_name = display_name
        profile.save()

    # JWT pair so the app is logged in
    token_ser = TokenObtainPairSerializer(data={"username": username, "password": password})
    token_ser.is_valid(raise_exception=True)
    tokens = token_ser.validated_data

    return Response(
        {
            "user": {
                "id": profile.id,
                "user": {"id": user.id, "username": user.username, "email": user.email},
                "display_name": profile.display_name,
                "rank": getattr(profile, "rank", "Bronze"),
                "xp": int(getattr(profile, "xp", 0) or 0),
            },
            "access": tokens.get("access"),
            "refresh": tokens.get("refresh"),
        },
        status=status.HTTP_201_CREATED,
    )