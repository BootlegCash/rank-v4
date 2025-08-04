from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import Profile, DailyLog, FriendRequest
from .serializers import (
    DailyLogSerializer,
    ProfileSerializer,
    FriendRequestSerializer
)
from datetime import date


def current_log_date():
    return date.today()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    profile = request.user.profile
    return Response({
        "username": request.user.username,
        "email": request.user.email,
        "xp": profile.xp,
        "rank": profile.rank,
        "beer": profile.beer,
        "floco": profile.floco,
        "rum": profile.rum,
        "whiskey": profile.whiskey,
        "vodka": profile.vodka,
        "tequila": profile.tequila,
        "shotguns": profile.shotguns,
        "snorkels": profile.snorkels,
        "thrown_up": profile.thrown_up,
        "total_alcohol": profile.calculate_alcohol_drank(),
    })


class DailyLogViewSet(viewsets.ModelViewSet):
    serializer_class = DailyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = current_log_date()
        return DailyLog.objects.filter(profile=self.request.user.profile, date=today)

    def perform_create(self, serializer):
        profile = self.request.user.profile
        today = current_log_date()
        daily_log, created = DailyLog.objects.get_or_create(profile=profile, date=today)
        data = serializer.validated_data

        daily_log.beer += data.get('beer', 0)
        daily_log.floco += data.get('floco', 0)
        daily_log.rum += data.get('rum', 0)
        daily_log.whiskey += data.get('whiskey', 0)
        daily_log.vodka += data.get('vodka', 0)
        daily_log.tequila += data.get('tequila', 0)
        daily_log.shotguns += data.get('shotguns', 0)
        daily_log.snorkels += data.get('snorkels', 0)
        if data.get('thrown_up', False):
            daily_log.thrown_up += 1

        daily_log.xp = daily_log.calculate_xp()
        daily_log.save()

        profile.beer += data.get('beer', 0)
        profile.floco += data.get('floco', 0)
        profile.rum += data.get('rum', 0)
        profile.whiskey += data.get('whiskey', 0)
        profile.vodka += data.get('vodka', 0)
        profile.tequila += data.get('tequila', 0)
        profile.shotguns += data.get('shotguns', 0)
        profile.snorkels += data.get('snorkels', 0)
        if data.get('thrown_up', False):
            profile.thrown_up += 1
        profile.save()


@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def register_api(request):
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password1 = request.data.get('password1', '')
    password2 = request.data.get('password2', '')
    display_name = request.data.get('display_name', '').strip()

    if not username or not email or not password1 or not password2:
        return Response({'error': 'All fields are required.'}, status=400)
    if password1 != password2:
        return Response({'error': 'Passwords do not match.'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password1)
    profile = Profile.objects.get(user=user)
    if display_name:
        profile.display_name = display_name
        profile.save()

    return Response({
        'success': True,
        'username': username,
        'email': email,
        'display_name': profile.display_name
    }, status=201)


# --- FRIEND API ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friend_list_api(request):
    profile = request.user.profile
    friends = profile.friends.all()
    serializer = ProfileSerializer(friends, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_friend_request_api(request):
    username = request.data.get('username')
    if not username:
        return Response({'error': 'Username is required.'}, status=400)

    try:
        to_user_profile = User.objects.get(username=username).profile
        from_profile = request.user.profile
        if to_user_profile == from_profile:
            return Response({'error': 'You cannot send a request to yourself.'}, status=400)
        if FriendRequest.objects.filter(from_user=from_profile, to_user=to_user_profile).exists():
            return Response({'error': 'Friend request already sent.'}, status=400)
        if to_user_profile in from_profile.friends.all():
            return Response({'error': 'You are already friends.'}, status=400)

        request_obj = FriendRequest.objects.create(from_user=from_profile, to_user=to_user_profile)
        return Response(FriendRequestSerializer(request_obj).data, status=201)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_friend_request_api(request):
    request_id = request.data.get('request_id')
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user.profile)
        friend_request.accept()
        return Response({'success': True})
    except FriendRequest.DoesNotExist:
        return Response({'error': 'Friend request not found.'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_friend_request_api(request):
    request_id = request.data.get('request_id')
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user.profile)
        friend_request.delete()
        return Response({'success': True})
    except FriendRequest.DoesNotExist:
        return Response({'error': 'Friend request not found.'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_friend_api(request):
    profile_id = request.data.get('profile_id')
    try:
        friend_profile = Profile.objects.get(id=profile_id)
        if friend_profile in request.user.profile.friends.all():
            request.user.profile.friends.remove(friend_profile)
            friend_profile.friends.remove(request.user.profile)
            return Response({'success': True})
        return Response({'error': 'Not friends.'}, status=400)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found.'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users_api(request):
    query = request.GET.get('q', '').strip()
    if query:
        users = Profile.objects.filter(user__username__icontains=query).exclude(user=request.user)[:10]
        serializer = ProfileSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)
    return Response([], status=200)
