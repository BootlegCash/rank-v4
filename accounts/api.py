# accounts/api.py
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Profile, FriendRequest
from .serializers import ProfileMiniSerializer, FriendRequestSerializer


# -------- Helpers --------
def _me(request) -> Profile:
    return request.user.profile


# -------- Me / Profile --------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current user’s profile details."""
    return Response(ProfileMiniSerializer(_me(request)).data)


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
