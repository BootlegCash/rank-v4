# accounts/api.py
from datetime import datetime

from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.templatetags.static import static

import calendar as cal_module
from datetime import datetime, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import RegisterSerializer
from .models import Profile, FriendRequest, DailyLog, current_log_date, Post
from .serializers import (
    ProfileMiniSerializer,
    ProfileSerializer,
    FriendRequestSerializer,
    DailyLogSerializer,
    PostSerializer,
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
    """
    Convert a relative URL/path into an absolute URL.
    If already absolute, keep it.
    """
    if not relurl:
        return ""
    if relurl.startswith("http://") or relurl.startswith("https://"):
        return relurl
    return request.build_absolute_uri(relurl)


def _safe_static_url(relpath: str) -> str:
    """
    Manifest-safe static():
    If CompressedManifestStaticFilesStorage can't find the entry, do NOT crash.
    """
    try:
        return static(relpath)  # may raise ValueError if not in manifest
    except Exception:
        # fallback to plain /static/...
        base = settings.STATIC_URL or "/static/"
        return f"{base}{relpath}".replace("//", "/")


def _static_abs(request, relpath: str) -> str:
    return _abs(request, _safe_static_url(relpath))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    profile = user.profile

    display_name = (getattr(profile, "display_name", "") or "").strip() \
                   or (getattr(user, "first_name", "") or "").strip() \
                   or user.username

    avatar_url = None
    if getattr(profile, "avatar", None):
        try:
            avatar_url = _abs(request, profile.avatar.url)
        except Exception:
            pass
    if not avatar_url:
        avatar_url = _static_abs(request, "img/avatar_placeholder.png")

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

        "beers": beer, "flocos": floco, "rums": rum,
        "whiskeys": whiskey, "vodkas": vodka, "tequilas": tequila,

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
    mep = _me(request)
    friends = mep.friends.all().order_by("user__username")
    return Response(ProfileMiniSerializer(friends, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def requests_list(request):
    mep = _me(request)
    received = FriendRequest.objects.filter(to_user=mep, accepted=False).order_by("-created_at")
    sent     = FriendRequest.objects.filter(from_user=mep, accepted=False).order_by("-created_at")
    return Response({
        "received": FriendRequestSerializer(received, many=True).data,
        "sent":     FriendRequestSerializer(sent, many=True).data,
    })


# -------- Friends: search / send / accept / reject / remove --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_search(request):
    q = (request.GET.get("q") or "").strip()
    mep = _me(request)
    if not q:
        return Response([], status=200)

    qs = Profile.objects.filter(user__username__icontains=q).exclude(id=mep.id)[:10]
    qs = [p for p in qs if p not in mep.friends.all()]
    return Response(ProfileMiniSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def send_request(request):
    mep = _me(request)
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)

    try:
        to = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    if to == mep:
        return Response({"detail": "cannot send request to yourself"}, status=400)
    if to in mep.friends.all():
        return Response({"detail": "already friends"}, status=409)
    if FriendRequest.objects.filter(from_user=mep, to_user=to, accepted=False).exists():
        return Response({"detail": "request already sent"}, status=409)
    if FriendRequest.objects.filter(from_user=to, to_user=mep, accepted=False).exists():
        return Response({"detail": "they already sent you a request"}, status=409)

    # Check if request already exists
    if FriendRequest.objects.filter(from_user=mep, to_user=to).exists():
        return Response({'error': 'Friend request already sent.'}, status=400)

    # Check if already friends
    if mep.friends.filter(id=to.id).exists():
        return Response({'error': 'Already friends.'}, status=400)

    fr = FriendRequest.objects.create(from_user=mep, to_user=to)
    return Response(FriendRequestSerializer(fr).data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def accept_request(request, request_id: int):
    mep = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=mep, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.accept()
    return Response({"detail": "friend request accepted"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reject_request(request, request_id: int):
    mep = _me(request)
    fr = FriendRequest.objects.filter(id=request_id, to_user=mep, accepted=False).first()
    if not fr:
        return Response({"detail": "request not found"}, status=404)
    fr.delete()
    return Response({"detail": "friend request rejected"}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def remove_friend(request):
    mep = _me(request)
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)
    try:
        other = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    if other not in mep.friends.all():
        return Response({"detail": "not friends"}, status=409)

    mep.friends.remove(other)
    other.friends.remove(mep)
    return Response({"detail": "removed from friends"}, status=200)


# -------- Drinks logging --------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def log_drink(request):
    mep = _me(request)

    raw_date = (request.data.get("date") or "").strip()
    if raw_date:
        try:
            log_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "date must be YYYY-MM-DD"}, status=400)
    else:
        log_date = current_log_date()

    fields = [
        "beer", "floco", "rum", "whiskey", "vodka", "tequila",
        "shotguns", "snorkels", "thrown_up",
    ]
    inc = {f: _safe_int(request.data.get(f), 0) for f in fields}

    if not any(inc.values()):
        return Response({"detail": "No changes supplied."}, status=400)

    for k, v in inc.items():
        if v < 0:
            return Response({k: "Must be >= 0"}, status=400)

    daily_log, _ = DailyLog.objects.get_or_create(profile=mep, date=log_date)
    for f, add in inc.items():
        setattr(daily_log, f, getattr(daily_log, f, 0) + add)
    daily_log.xp = daily_log.calculate_xp()
    daily_log.save()

    for f, add in inc.items():
        if hasattr(mep, f):
            setattr(mep, f, getattr(mep, f, 0) + add)
    mep.save()

    return Response(
        {
            "profile": ProfileSerializer(mep).data,
            "daily_log": DailyLogSerializer(daily_log).data,
            "detail": "Logged successfully.",
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def register(request):
    ser = RegisterSerializer(data=request.data)
    if not ser.is_valid():
        return Response({"detail": ser.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = ser.validated_data

    username = (data.get("username") or "").strip()
    if not username:
        return Response({"detail": {"username": ["Username is required."]}}, status=400)

    password = (
        data.get("password")
        or data.get("password1")
        or data.get("pass")
        or data.get("pwd")
        or request.data.get("password")
        or request.data.get("password1")
        or request.data.get("pass")
        or request.data.get("pwd")
    )

    password2 = (
        data.get("password2")
        or data.get("confirm_password")
        or data.get("confirmPassword")
        or request.data.get("password2")
        or request.data.get("confirm_password")
        or request.data.get("confirmPassword")
    )

    if not password:
        return Response({"detail": {"password": ["Password is required."]}}, status=400)

    if password2 is not None and str(password2) != str(password):
        return Response({"detail": {"password2": ["Passwords do not match."]}}, status=400)

    email = (data.get("email") or "").strip()
    display_name = (data.get("display_name") or "").strip() or username

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
    )

    profile = getattr(user, "profile", None)

    def is_placeholder_name(name):
        if not name:
            return True
        name = str(name).strip()
        return (not name) or name.lower() == "user"

    if profile is None:
        profile = Profile.objects.create(user=user, display_name=display_name)
    elif is_placeholder_name(getattr(profile, "display_name", None)):
        profile.display_name = display_name
        profile.save()

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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def cancel_request(request):
    mep = request.user.profile
    username = (request.data.get("username") or "").strip()
    if not username:
        return Response({"detail": "username is required"}, status=400)

    try:
        to = User.objects.get(username=username).profile
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    fr = FriendRequest.objects.filter(from_user=mep, to_user=to, accepted=False).first()
    if not fr:
        return Response({"detail": "no pending request to cancel"}, status=404)
    fr.delete()
    return Response({"detail": "request cancelled"}, status=200)


# --- FRIEND PUBLIC PROFILE (by username) ---
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def friend_profile_api(request, username: str):
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({"detail": "user not found"}, status=404)

    p = target_user.profile
    display_name = (getattr(p, "display_name", "") or "").strip() or target_user.username

    avatar_url = None
    if getattr(p, "avatar", None):
        try:
            avatar_url = _abs(request, p.avatar.url)
        except Exception:
            pass
    if not avatar_url:
        avatar_url = _static_abs(request, "img/avatar_placeholder.png")

    beer     = int(getattr(p, "beer", 0) or 0)
    floco    = int(getattr(p, "floco", 0) or 0)
    rum      = int(getattr(p, "rum", 0) or 0)
    whiskey  = int(getattr(p, "whiskey", 0) or 0)
    vodka    = int(getattr(p, "vodka", 0) or 0)
    tequila  = int(getattr(p, "tequila", 0) or 0)
    total    = beer + floco + rum + whiskey + vodka + tequila

    shotguns = int(getattr(p, "shotguns", 0) or 0)
    snorkels = int(getattr(p, "snorkels", 0) or 0)
    thrown   = int(getattr(p, "thrown_up", 0) or 0)

    rank_name    = getattr(p, "rank", "Bronze")
    xp           = int(getattr(p, "xp", 0) or 0)
    next_rank_xp = int(getattr(p, "next_rank_xp", 600) or 600)

    mep = request.user.profile
    are_friends = p in mep.friends.all()

    return Response({
        "username": target_user.username,
        "email": target_user.email or "",
        "display_name": display_name,
        "avatar_url": avatar_url,
        "rank": rank_name,
        "xp": xp,
        "next_rank_xp": next_rank_xp,
        "beer": beer, "floco": floco, "rum": rum,
        "whiskey": whiskey, "vodka": vodka, "tequila": tequila,
        "total_drinks": total,
        "shotguns": shotguns, "snorkels": snorkels, "thrown_up": thrown,
        "are_friends": are_friends,
    }, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    mep = request.user.profile

    profiles = list(mep.friends.all()) + [mep]
    seen_ids = set()
    unique_profiles = []
    for p in profiles:
        if p.id not in seen_ids:
            seen_ids.add(p.id)
            unique_profiles.append(p)

    unique_profiles.sort(key=lambda p: (-p.xp, p.user.username.lower()))

    data = []
    for idx, p in enumerate(unique_profiles, start=1):
        data.append({
            "position": idx,
            "is_me": (p.id == mep.id),
            "id": p.id,
            "username": p.user.username,
            "display_name": p.display_name or p.user.username,
            "rank": p.rank,
            "xp": p.xp,
        })

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feed(request):
    mep = request.user.profile

    friend_ids = list(mep.friends.values_list("id", flat=True))
    profile_ids = friend_ids + [mep.id]

    qs = (
        Post.objects.filter(user_id__in=profile_ids)
        .select_related("user__user")
        .prefetch_related("likes")
        .order_by("-created_at")[:50]
    )

    serializer = PostSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_post(request):
    content = (request.data.get("content") or "").strip()
    if not content:
        return Response({"detail": "content is required"}, status=400)

    mep = request.user.profile
    post = Post.objects.create(user=mep, content=content)

    serializer = PostSerializer(post, context={"request": request})
    return Response(serializer.data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def like_post_api(request, post_id: int):
    mep = request.user.profile
    post = get_object_or_404(Post, id=post_id)

    if post.likes.filter(id=mep.id).exists():
        post.likes.remove(mep)
        liked = False
    else:
        post.likes.add(mep)
        liked = True

    return Response(
        {
            "id": post.id,
            "liked": liked,
            "like_count": post.likes.count(),
        },
        status=200,
    )



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_calendar_api(request, year=None, month=None):
    profile = _me(request)
    from django.utils import timezone

    now = timezone.localtime(timezone.now())
    today = now.date()

    if not year:
        year = today.year
    if not month:
        month = today.month

    year = int(year)
    month = int(month)

    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)

    logs_for_month = DailyLog.objects.filter(
        profile=profile,
        date__gte=first_day,
        date__lte=last_day
    )

    logs_map = {log.date.isoformat(): DailyLogSerializer(log).data for log in logs_for_month}

    cal = cal_module.Calendar(firstweekday=6)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_data = []
        for day in week:
            week_data.append({
                "date": day.isoformat(),
                "day": day.day,
                "is_current_month": day.month == month,
                "is_today": day == today,
                "log": logs_map.get(day.isoformat()),
            })
        weeks.append(week_data)

    prev = (first_day - timedelta(days=1))
    next_ = (last_day + timedelta(days=1))

    return Response({
        "year": year,
        "month": month,
        "month_name": cal_module.month_name[month],
        "today": today.isoformat(),
        "prev_year": prev.year,
        "prev_month": prev.month,
        "next_year": next_.year,
        "next_month": next_.month,
        "weeks": weeks,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def day_log_detail_api(request, year, month, day):
    profile = _me(request)
    try:
        log_date = datetime(int(year), int(month), int(day)).date()
    except ValueError:
        return Response({"detail": "Invalid date"}, status=400)

    try:
        daily_log = DailyLog.objects.get(profile=profile, date=log_date)
        return Response({"date": log_date.isoformat(), "log": DailyLogSerializer(daily_log).data})
    except DailyLog.DoesNotExist:
        return Response({"date": log_date.isoformat(), "log": None})