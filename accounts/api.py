# accounts/api.py
from datetime import date as _date

from django.contrib.auth.models import User
from django.db import transaction
from django.templatetags.static import static

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Profile, FriendRequest, DailyLog
from .serializers import (
    ProfileMiniSerializer,
    FriendRequestSerializer,
    ProfilePublicSerializer,
    LogDrinkRequestSerializer,
    LogDrinkResponseSerializer,
)

# -------- Helpers --------
def _me(request) -> Profile:
    return request.user.profile

def _abs(request, relurl: str) -> str:
    """Make any relative /static/... or /media/... absolute for the app."""
    return request.build_absolute_uri(relurl)

def _static_abs(request, relpath: str) -> str:
    return _abs(request, static(relpath))


# -------- Me / Profile --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /accounts/api/profile/
    Returns stable mobile payload including display_name and ABSOLUTE avatar_url.
    Falls back to a static placeholder if no uploaded avatar exists.
    """
    user = request.user
    profile = getattr(user, "profile", None)

    # Display name resolution
    display_name = None
    if profile and getattr(profile, "display_name", None):
        display_name = profile.display_name
    if not display_name:
        display_name = (getattr(user, "first_name", "") or "").strip() or None
    if not display_name:
        display_name = getattr(user, "username", "") or "User"

    # Avatar: prefer uploaded; else static placeholder
    avatar_url = None
    if profile and hasattr(profile, "avatar") and profile.avatar:
        try:
            avatar_url = _abs(request, profile.avatar.url)
        except Exception:
            avatar_url = None
    if not avatar_url:
        # Ensure this file exists at static/img/avatar_placeholder.png
        avatar_url = _static_abs(request, "img/avatar_placeholder.png")

    rank_name = getattr(profile, "rank", "Bronze")
    xp = int(getattr(profile, "xp", 0) or 0)
    next_rank_xp = int(getattr(profile, "next_rank_xp", 1181) or 1181)

    payload = {
        "username": user.username,
        "email": user.email or "",
        "display_name": display_name,
        "avatar_url": avatar_url,
        "rank": rank_name,
        "xp": xp,
        "next_rank_xp": next_rank_xp,
    }
    return Response(ProfilePublicSerializer(payload).data, status=status.HTTP_200_OK)


# -------- Friends: lists --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def friends_list(request):
    me_profile = _me(request)
    friends = me_profile.friends.all().order_by("user__username")
    return Response(ProfileMiniSerializer(friends, many=True).data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def requests_list(request):
    me_profile = _me(request)
    received = FriendRequest.objects.filter(to_user=me_profile, accepted=False).order_by("-created_at")
    sent     = FriendRequest.objects.filter(from_user=me_profile, accepted=False).order_by("-created_at")
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
    me_profile = _me(request)
    if not q:
        return Response([], status=200)
    qs = Profile.objects.filter(user__username__icontains=q).exclude(id=me_profile.id)[:10]
    # exclude already-friends
    qs = [p for p in qs if p not in me_profile.friends.all()]
    return Response(ProfileMiniSerializer(qs, many=True).data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def send_request(request):
    """JSON: { "username": "target" }"""
    me_profile = _me(request)
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)

    try:
        to = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    if to == me_profile:
        return Response({"detail": "cannot send request to yourself"}, status=400)
    if to in me_profile.friends.all():
        return Response({"detail": "already friends"}, status=409)
    if FriendRequest.objects.filter(from_user=me_profile, to_user=to, accepted=False).exists():
        return Response({"detail": "request already sent"}, status=409)
    if FriendRequest.objects.filter(from_user=to, to_user=me_profile, accepted=False).exists():
        return Response({"detail": "they already sent you a request"}, status=409)

    fr = FriendRequest.objects.create(from_user=me_profile, to_user=to)  # pending
    return Response(FriendRequestSerializer(fr).data, status=201)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def accept_request(request, request_id: int):
    me_profile = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=me_profile, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.accept()  # establishes mutual friendship
    return Response({"detail": "friend request accepted"}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reject_request(request, request_id: int):
    me_profile = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=me_profile, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.delete()
    return Response({"detail": "friend request rejected"}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def remove_friend(request):
    """JSON: { "username": "target" }  – removes both directions."""
    me_profile = _me(request)
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)
    try:
        other = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    if other not in me_profile.friends.all():
        return Response({"detail": "not friends"}, status=409)

    me_profile.friends.remove(other)
    other.friends.remove(me_profile)
    return Response({"detail": "removed from friends"}, status=200)


# -------- Drinks: log_drink --------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def log_drink(request):
    """
    POST /accounts/api/log_drink/
    Body:
    {
      "drink_name": "Beer",
      "abv_percent": 5.0,
      "volume_oz": 12,
      "count": 1,
      "shotguns": 0,
      "snorkels": 0,
      "notes": "Game night"
    }
    Returns 201 with computed standard drinks. Optionally updates today's DailyLog and Profile.
    """
    ser = LogDrinkRequestSerializer(data=request.data)
    if not ser.is_valid():
        return Response({"detail": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    data = ser.validated_data

    drink_name = data["drink_name"].strip()
    abv = float(data["abv_percent"])
    volume_oz = float(data["volume_oz"])
    count = int(data.get("count", 1))
    shotguns = int(data.get("shotguns", 0))
    snorkels = int(data.get("snorkels", 0))
    notes = data.get("notes", "").strip()

    # NIAAA approx for a "standard drink"
    std_per = (abv / 100.0) * (volume_oz * 29.5735) / 14.0
    total_std = std_per * count

    # Optional persistence (safe no-ops if fields missing)
    try:
        profile: Profile = request.user.profile  # type: ignore
    except Exception:
        profile = None

    try:
        if profile is not None:
            today = _date.today()
            daily, _ = DailyLog.objects.get_or_create(profile=profile, date=today)

            # Increment known drink fields if they exist
            drink_map = {
                "beer": "beer",
                "floco": "floco",
                "rum": "rum",
                "whiskey": "whiskey",
                "vodka": "vodka",
                "tequila": "tequila",
            }
            key = drink_map.get(drink_name.lower())
            if key and hasattr(daily, key):
                setattr(daily, key, (getattr(daily, key) or 0) + count)

            if hasattr(daily, "shotguns"):
                daily.shotguns = (daily.shotguns or 0) + shotguns
            if hasattr(daily, "snorkels"):
                daily.snorkels = (daily.snorkels or 0) + snorkels
            daily.save()

            if hasattr(profile, "total_drinks"):
                profile.total_drinks = (profile.total_drinks or 0) + count
            if hasattr(profile, "shotguns"):
                profile.shotguns = (profile.shotguns or 0) + shotguns
            if hasattr(profile, "snorkels"):
                profile.snorkels = (profile.snorkels or 0) + snorkels
            if hasattr(profile, "xp"):
                # naive XP example; swap for your real formula when ready
                profile.xp = (profile.xp or 0) + int(round(total_std * 10))
            profile.save()
    except Exception:
        # Don't fail the API if counters save fails
        pass

    resp = {
        "ok": True,
        "message": "Drink logged.",
        "drink_name": drink_name,
        "abv_percent": abv,
        "volume_oz": volume_oz,
        "count": count,
        "shotguns": shotguns,
        "snorkels": snorkels,
        "notes": notes,
        "computed": {
            "std_drinks_per_item": round(std_per, 3),
            "total_std_drinks": round(total_std, 3),
        },
    }
    return Response(LogDrinkResponseSerializer(resp).data, status=status.HTTP_201_CREATED)
