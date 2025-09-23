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


# ------------------ Helpers ------------------

def _me(request) -> Profile:
    return request.user.profile

def _abs(request, relurl: str) -> str:
    """Turn a relative /static/... or /media/... URL into an absolute URL."""
    return request.build_absolute_uri(relurl)

def _static_abs(request, relpath: str) -> str:
    return _abs(request, static(relpath))


# ------------------ Me / Profile ------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /accounts/api/profile/

    Returns:
      - username, email, display_name
      - rank, xp, next_rank_xp
      - avatar_url (absolute; static fallback)
      - drink counters: beer, floco, rum, whiskey, vodka, tequila
      - aliases (beers, flocos, rums, whiskeys, vodkas, tequilas)
      - total_drinks, shotguns, snorkels, thrown_up
    """
    user = request.user
    profile = getattr(user, "profile", None)

    # Display name
    display_name = None
    if profile and getattr(profile, "display_name", None):
        display_name = profile.display_name
    if not display_name:
        display_name = (getattr(user, "first_name", "") or "").strip() or None
    if not display_name:
        display_name = getattr(user, "username", "") or "User"

    # Avatar
    avatar_url = None
    if profile and hasattr(profile, "avatar") and profile.avatar:
        try:
            avatar_url = _abs(request, profile.avatar.url)
        except Exception:
            avatar_url = None
    if not avatar_url:
        avatar_url = _static_abs(request, "img/avatar_placeholder.png")

    # Rank / XP
    rank_name = getattr(profile, "rank", "Bronze")
    xp = int(getattr(profile, "xp", 0) or 0)
    next_rank_xp = int(getattr(profile, "next_rank_xp", 1181) or 1181)

    # Counters
    beer     = int(getattr(profile, "beer", 0) or 0)
    floco    = int(getattr(profile, "floco", 0) or 0)
    rum      = int(getattr(profile, "rum", 0) or 0)
    whiskey  = int(getattr(profile, "whiskey", 0) or 0)
    vodka    = int(getattr(profile, "vodka", 0) or 0)
    tequila  = int(getattr(profile, "tequila", 0) or 0)

    total_drinks = int(getattr(profile, "total_drinks", 0) or 0)
    shotguns     = int(getattr(profile, "shotguns", 0) or 0)
    snorkels     = int(getattr(profile, "snorkels", 0) or 0)
    thrown_up    = int(getattr(profile, "thrown_up", 0) or 0)

    # Build payload with a stable core + extras
    core = ProfilePublicSerializer({
        "username": user.username,
        "email": user.email or "",
        "display_name": display_name,
        "avatar_url": avatar_url,
        "rank": rank_name,
        "xp": xp,
        "next_rank_xp": next_rank_xp,
    }).data

    extras = {
        "beer": beer, "floco": floco, "rum": rum, "whiskey": whiskey, "vodka": vodka, "tequila": tequila,
        "beers": beer, "flocos": floco, "rums": rum, "whiskeys": whiskey, "vodkas": vodka, "tequilas": tequila,
        "total_drinks": total_drinks,
        "shotguns": shotguns,
        "snorkels": snorkels,
        "thrown_up": thrown_up,
    }
    core.update(extras)
    return Response(core, status=status.HTTP_200_OK)


# ------------------ Friends: lists ------------------

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


# ------------------ Friends: search / send / accept / reject / remove ------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_search(request):
    q = (request.GET.get("q") or "").strip()
    me_profile = _me(request)
    if not q:
        return Response([], status=200)
    qs = Profile.objects.filter(user__username__icontains=q).exclude(id=me_profile.id)[:10]
    qs = [p for p in qs if p not in me_profile.friends.all()]
    return Response(ProfileMiniSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def send_request(request):
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

    fr = FriendRequest.objects.create(from_user=me_profile, to_user=to)
    return Response(FriendRequestSerializer(fr).data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def accept_request(request, request_id: int):
    me_profile = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=me_profile, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.accept()
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


# ------------------ Drinks: log_drink ------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def log_drink(request):
    """
    POST /accounts/api/log_drink/

    Accepts either:
      - Detailed: {"drink_name": "...", "abv_percent": 5.0, "volume_oz": 12, "count": 1, ...}
      - Shortcut: {"category": "beer", "count": 1, ...}

    Returns computed standard drinks, and (if models permit) increments today's DailyLog and Profile counters.
    """
    ser = LogDrinkRequestSerializer(data=request.data)
    if not ser.is_valid():
        return Response({"detail": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    data = ser.validated_data

    count    = int(data.get("count", 1))
    shotguns = int(data.get("shotguns", 0))
    snorkels = int(data.get("snorkels", 0))
    notes    = (data.get("notes") or "").strip()

    # Defaults used for category shortcut
    category_defaults = {
        "beer":    (5.0, 12.0),
        "floco":   (6.0, 12.0),
        "rum":     (40.0, 1.5),
        "whiskey": (40.0, 1.5),
        "vodka":   (40.0, 1.5),
        "tequila": (40.0, 1.5),
    }

    category = data.get("category")
    if category:
        drink_name  = category.capitalize()
        abv_percent, volume_oz = category_defaults[category]
    else:
        drink_name  = (data.get("drink_name") or "").strip()
        abv_percent = float(data["abv_percent"])
        volume_oz   = float(data["volume_oz"])

    # Compute standard drinks (NIAAA-ish)
    std_per  = (abv_percent / 100.0) * (volume_oz * 29.5735) / 14.0
    total_std = std_per * count

    # Persist counters if models exist
    try:
        profile: Profile = request.user.profile  # type: ignore
    except Exception:
        profile = None

    try:
        if profile is not None:
            today = _date.today()
            daily, _ = DailyLog.objects.get_or_create(profile=profile, date=today)

            if category and hasattr(daily, category):
                setattr(daily, category, (getattr(daily, category) or 0) + count)

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
                profile.xp = (profile.xp or 0) + int(round(total_std * 10))
            profile.save()
    except Exception:
        # Don't fail the call if persistence hiccups
        pass

    resp = {
        "ok": True,
        "message": "Drink logged.",
        "drink_name": drink_name,
        "abv_percent": abv_percent,
        "volume_oz": volume_oz,
        "category": category or "",
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
