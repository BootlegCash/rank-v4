import calendar
import random
from datetime import date, datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import views as auth_views


from achievements.models import Achievement
from .forms import RegistrationForm, StatsUpdateForm, SendFriendRequestForm, PostForm, DailyLogForm
from .models import Profile, FriendRequest, Post, DailyLog, current_log_date

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response

def register(request):
    if request.user.is_authenticated:
        return redirect('welcome')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('welcome')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('welcome')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        UserModel = get_user_model()
        if not UserModel.objects.filter(username=username).exists():
            messages.error(request, 'Account not found')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('welcome')
            else:
                messages.error(request, 'Invalid password')
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('login')

@login_required
def profile(request):
    profile_obj = get_object_or_404(Profile, user=request.user)
    earned_achievements = profile_obj.check_achievements()
    return render(request, 'accounts/profile.html', {
        'profile': profile_obj,
        'achievements': earned_achievements,
    })


@login_required
def update_stats(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = StatsUpdateForm(request.POST)
        if form.is_valid():
            # Update the overall profile cumulatively.
            for field, increment in form.cleaned_data.items():
                current_val = getattr(profile, field, 0)
                setattr(profile, field, current_val + increment)
            profile.save()
            
            # Get or create the daily log using our custom date logic.
            log_date = current_log_date()  # This adjusts for your 3 AM to 3 AM day boundary.
            daily_log, created = DailyLog.objects.get_or_create(profile=profile, date=log_date)
            
            # Add the increments to the daily log.
            for field, increment in form.cleaned_data.items():
                current_log_val = getattr(daily_log, field, 0)
                setattr(daily_log, field, current_log_val + increment)
            daily_log.xp = daily_log.calculate_xp()
            daily_log.save()

            messages.success(request, 'Stats updated!')
            return redirect('profile')
    else:
        form = StatsUpdateForm()
    
    return render(request, 'accounts/update_stats.html', {'form': form})



@login_required
def leaderboard(request):
    profile_obj = get_object_or_404(Profile, user=request.user)
    friends = profile_obj.friends.all()
    friend_profiles = Profile.objects.filter(user__in=[f.user for f in friends]).order_by('-xp')
    return render(request, 'accounts/leaderboard.html', {
        'profiles': friend_profiles,
        'user_profile': profile_obj
    })

@login_required
def friend_list(request):
    profile_obj = get_object_or_404(Profile, user=request.user)

    received_requests = FriendRequest.objects.filter(
        to_user=profile_obj, accepted=False
    )
    sent_requests = FriendRequest.objects.filter(
        from_user=profile_obj, accepted=False
    )

    return render(request, 'accounts/friend_list.html', {
        'friends': profile_obj.friends.all(),
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    })


@login_required
def send_friend_request(request):
    if request.method == 'POST':
        form = SendFriendRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                to_user_profile = User.objects.get(username=username).profile
                if to_user_profile == request.user.profile:
                    messages.error(request, "You can't send a request to yourself")
                elif FriendRequest.objects.filter(
                    from_user=request.user.profile, to_user=to_user_profile
                ).exists():
                    messages.error(request, "Friend request already sent")
                elif to_user_profile in request.user.profile.friends.all():
                    messages.error(request, "You're already friends")
                else:
                    # CREATE THE FRIEND REQUEST
                    FriendRequest.objects.create(
                        from_user=request.user.profile,
                        to_user=to_user_profile
                    )
                    messages.success(request, 'Friend request sent!')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
            return redirect('friend_list')
    else:
        form = SendFriendRequestForm()

    return render(request, 'accounts/send_friend_request.html', {'form': form})



@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user.profile)
    try:
        friend_request.accept()
        messages.success(request, f"You're now friends with {friend_request.from_user.user.username}!")
    except Exception as e:
        messages.error(request, f"Error accepting request: {str(e)}")
    return redirect('friend_list')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user.profile)
    friend_request.delete()
    messages.success(request, "Friend request rejected")
    return redirect('friend_list')

@login_required
def friend_list(request):
    profile_obj = get_object_or_404(Profile, user=request.user)

    received_requests = FriendRequest.objects.filter(
        to_user=profile_obj, accepted=False
    )
    sent_requests = FriendRequest.objects.filter(
        from_user=profile_obj, accepted=False
    )

    return render(request, 'accounts/friend_list.html', {
        'friends': profile_obj.friends.all(),
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    })

@login_required
@require_POST
def remove_friend(request, profile_id):
    friend_profile_obj = get_object_or_404(Profile, id=profile_id)
    if friend_profile_obj in request.user.profile.friends.all():
        request.user.profile.friends.remove(friend_profile_obj)
        friend_profile_obj.friends.remove(request.user.profile)
        messages.success(request, f"You have removed {friend_profile_obj.user.username} from your friends.")
    else:
        messages.error(request, "This user is not in your friend list.")
    return redirect('friend_list')

@login_required
def wheel_of_dares(request):
    DARES = [
        "Take a waterfall shot!",
        "Do your best dance for 30 seconds",
        "Tell an embarrassing story",
        "Sing the chorus of your favorite song",
        "Arm wrestle the person to your left"
    ]
    if request.method == 'POST':
        dare = random.choice(DARES)
        profile_obj = request.user.profile
        profile_obj.xp += 25  # Bonus XP for completing the dare
        profile_obj.save()
        return render(request, 'accounts/wheel_result.html', {'dare': dare})
    return render(request, 'accounts/wheel_spin.html')

@login_required
def welcome(request):
    friend_posts = Post.objects.filter(user__in=request.user.profile.friends.all()).order_by('-created_at')
    user_posts = Post.objects.filter(user=request.user.profile).order_by('-created_at')
    all_posts = (friend_posts | user_posts).distinct().order_by('-created_at')
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user.profile
            post.save()
            return redirect('welcome')
    else:
        form = PostForm()
    return render(request, 'accounts/welcome.html', {'posts': all_posts, 'form': form})

@require_POST
@login_required
def like_post(request, post_id):
    post_obj = get_object_or_404(Post, id=post_id)
    profile_obj = request.user.profile
    if profile_obj in post_obj.likes.all():
        post_obj.likes.remove(profile_obj)
        liked = False
    else:
        post_obj.likes.add(profile_obj)
        liked = True
    return JsonResponse({
        'liked': liked,
        'like_count': post_obj.likes.count()
    })

class CreatePostView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'accounts/compose_post.html'
    success_url = reverse_lazy('welcome')

    def form_valid(self, form):
        form.instance.user = self.request.user.profile
        return super().form_valid(form)

def safety_guidelines(request):
    return render(request, 'accounts/safety_guidelines.html')

# --- Added "about" view to resolve the URL error ---
@login_required
def about(request):
    # Render a simple about page; ensure that you have an 'accounts/about.html' template
    return render(request, 'accounts/about.html')


@login_required
def achievements(request):
    
    from .models import Post

    profile_obj = request.user.profile
    all_achievements = Achievement.objects.all()
    earned = profile_obj.check_achievements()

    # Mapping: achievement code to (attribute, target value)
    # For the "post_count", we count posts by the user.
    progress_requirements = {
        "BEER_BEGINNER": ("beer", 10),
        "WHISKEY_WARRIOR": ("whiskey", 25),
        "RUM_RUNNER": ("rum", 20),
    }

    # Calculate post count for achievements that count posts
    post_count = Post.objects.filter(user=profile_obj).count()

    achievements_list = []
    for achievement in all_achievements:
        is_earned = achievement in earned
        progress = 0
        if achievement.code in progress_requirements:
            attr, target = progress_requirements[achievement.code]
            # For friends, count the number of friend relations
            if attr == "friends":
                value = profile_obj.friends.count()
            # For post_count, use the computed post_count
            elif attr == "post_count":
                value = post_count
            else:
                # For other attributes, get the value from profile (defaulting to 0)
                value = getattr(profile_obj, attr, 0)
            # Compute percentage; cap at 100%
            progress = min(100, int((value / target) * 100))
        else:
            progress = 100 if is_earned else 0

        achievements_list.append({
            'achievement': achievement,
            'is_earned': is_earned,
            'progress': progress
        })

    return render(request, 'accounts/achievements.html', {
        'achievements_list': achievements_list
    })


@login_required
def friend_search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        # Exclude yourself
        results = Profile.objects.filter(
            user__username__icontains=query
        ).exclude(user=request.user)[:5]
    return render(request, 'accounts/friend_search.html', {
        'query': query,
        'results': results
    })


@login_required
def friend_profile(request, username):
    """
    Displays a full profile for a friend, including stats and achievements.
    Shows a button to add or remove the friend based on the friendship status.
    """
    friend_profile_obj = get_object_or_404(Profile, user__username=username)
    is_friend = friend_profile_obj in request.user.profile.friends.all()
    # Optionally, if you want to pass achievements:
    earned_achievements = friend_profile_obj.check_achievements()
    
    return render(request, 'accounts/friend_profile.html', {
        'friend_profile': friend_profile_obj,
        'is_friend': is_friend,
        'achievements': earned_achievements,  # if you're showing achievements here
    })


@login_required
def update_daily_log(request):
    profile = get_object_or_404(Profile, user=request.user)
    log_date = current_log_date()  # uses the helper function from models
    daily_log, created = DailyLog.objects.get_or_create(profile=profile, date=log_date)
    
    if request.method == "POST":
        form = DailyLogForm(request.POST)
        if form.is_valid():
            # Update each field by adding the increment to the existing value.
            for field, increment in form.cleaned_data.items():
                current_val = getattr(daily_log, field, 0)
                setattr(daily_log, field, current_val + increment)
            daily_log.xp = daily_log.calculate_xp()
            daily_log.save()
            messages.success(request, "Today's log updated!")
            return redirect('profile')
    else:
        form = DailyLogForm()
    
    return render(request, "accounts/update_daily_log.html", {"form": form, "daily_log": daily_log})

@login_required
def daily_log_calendar(request):
    profile = get_object_or_404(Profile, user=request.user)
    logs = profile.daily_logs.all()
    return render(request, "accounts/daily_log_calendar.html", {"logs": logs})

@login_required
def monthly_calendar(request, year=None, month=None):
    profile = get_object_or_404(Profile, user=request.user)
    
    # Get current time in Arizona
    now = timezone.localtime(timezone.now())
    today = now.date()
    
    # Default to current month if not provided
    if not year:
        year = today.year
    if not month:
        month = today.month

    year = int(year)
    month = int(month)

    # Calculate the first and last day of the month (adjusted for 3 AM boundary)
    first_day = datetime(year, month, 1, 3, 0, 0)  # 3 AM on first day
    if month == 12:
        last_day = datetime(year+1, 1, 1, 2, 59, 59)  # 2:59:59 AM on Jan 1
    else:
        last_day = datetime(year, month+1, 1, 2, 59, 59)  # 2:59:59 AM on first of next month

    # Get logs for the month (adjusted for 3 AM boundary)
    logs_for_month = DailyLog.objects.filter(
        profile=profile,
        date__gte=first_day.date(),
        date__lte=last_day.date()
    )
    
    # Create a list of weeks where each day has its log data
    cal = calendar.Calendar(firstweekday=6)  # Sunday first
    month_weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_days = []
        for day in week:
            log = next((l for l in logs_for_month if l.date == day), None)
            week_days.append({
                'date': day,
                'day': day.day,
                'is_current_month': day.month == month,
                'is_today': day == today,
                'log': log
            })
        month_weeks.append(week_days)

    # Prepare navigation for previous/next month
    prev_month = (first_day - timedelta(days=1)).month
    prev_year = (first_day - timedelta(days=1)).year
    next_month = (last_day + timedelta(days=1)).month
    next_year = (last_day + timedelta(days=1)).year

    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'weeks': month_weeks,
        'today': today,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    }
    return render(request, "accounts/monthly_calendar.html", context)

@login_required
def day_log_detail(request, year, month, day):
    """
    Displays the DailyLog for a specific day (using the year, month, day from the calendar).
    If no log exists for that day, you can decide whether to show an empty log or a message.
    """
    profile = get_object_or_404(Profile, user=request.user)
    try:
        log_date = datetime(year, month, day).date()
    except ValueError:
        return render(request, 'accounts/day_log_detail.html', {'error': 'Invalid date'})

    daily_log = DailyLog.objects.filter(profile=profile, date=log_date).first()
    return render(request, 'accounts/day_log_detail.html', {
        'log_date': log_date,
        'daily_log': daily_log,
    })


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile_api(request):
    profile = request.user.profile
    return Response({
        "username": profile.user.username,
        "display_name": profile.display_name,
        "xp": profile.xp,
        "rank": profile.rank,
    })

class NeonPasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/emails/password_reset_form.html"
    email_template_name = "accounts/emails/password_reset_email.html"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    html_email_template_name = "accounts/emails/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class NeonPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/emails/password_reset_done.html"


class NeonPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """
    IMPORTANT:
    - If the token is invalid/expired, Django sets `validlink = False`.
    - We still render our template, and the template will show the request form instead.
    """
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Always provide a request form so invalid links can show "request new link" UI
        ctx["request_form"] = PasswordResetForm()
        ctx["request_post_url"] = reverse_lazy("password_reset")
        return ctx


class NeonPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


# ─────────────────────────────────────────────
# COIN FLIP GAME (session-based mock)
# ─────────────────────────────────────────────

TOKEN_THRESHOLDS = [
    (3,  1),
    (6,  2),
    (10, 4),
    (15, 7),
]

COIN_SHOP_ITEMS = [
    {"key": "force_shot",        "name": "Force Shot",        "cost": 3, "desc": "Force a friend to take a shot",             "needs_target": True},
    {"key": "streak_breaker",    "name": "Streak Breaker",    "cost": 5, "desc": "Reset a friend's win streak to 0",          "needs_target": True},
    {"key": "double_punishment", "name": "Double Punishment", "cost": 4, "desc": "Friend's next loss = 2 shots instead of 1", "needs_target": True},
    {"key": "shield",            "name": "Shield",            "cost": 6, "desc": "Block your next shot penalty",              "needs_target": False},
    {"key": "token_heist",       "name": "Token Heist",       "cost": 8, "desc": "Steal 2 tokens from a friend",              "needs_target": True},
]

DEFAULT_SIM_FRIENDS = ["Jake", "Trey", "Maddie", "Soph"]


def _init_game(session):
    if "coin_game" not in session:
        friends = []
        for name in DEFAULT_SIM_FRIENDS:
            friends.append({
                "name": name,
                "tokens": random.randint(3, 12),
                "streak": random.randint(0, 4),
                "shots_owed": 0,
                "double_punishment": False,
                "bs_tendency": round(random.uniform(0.05, 0.30), 2),
            })
        session["coin_game"] = {
            "tokens": 5,
            "lifetime_earned": 5,
            "lifetime_spent": 0,
            "total_flips": 0,
            "wins": 0,
            "losses": 0,
            "streak": 0,
            "best_streak": 0,
            "pending_shots": 0,
            "confirmed_shots": 0,
            "disputed_shots": 0,
            "shot_sources": "",
            "has_shield": False,
            "double_punishment": False,
            "challenges_won": 0,
            "challenges_lost": 0,
            "total_drinks": 0,
            "friends": friends,
        }
    return session["coin_game"]


def _streak_multiplier(streak):
    if streak >= 5:
        return 4
    elif streak >= 3:
        return 3
    return 1


def _tokens_for_drinks(count):
    earned = 0
    for threshold, tokens in TOKEN_THRESHOLDS:
        if count >= threshold:
            earned = tokens
    return earned


def _do_flip(game, bet):
    game["tokens"] -= bet
    game["lifetime_spent"] += bet
    game["total_flips"] += 1

    result = random.choice(["heads", "tails"])
    call = random.choice(["heads", "tails"])
    won = result == call
    shielded = False
    double = False
    multiplier = 1

    if won:
        multiplier = _streak_multiplier(game["streak"])
        payout = bet * 2 * multiplier
        game["tokens"] += payout
        game["lifetime_earned"] += payout
        game["wins"] += 1
        game["streak"] += 1
        game["best_streak"] = max(game["streak"], game["best_streak"])
        net = payout - bet
    else:
        game["losses"] += 1
        game["streak"] = 0
        net = -bet

        if game["has_shield"]:
            game["has_shield"] = False
            shielded = True
        else:
            shot_count = 2 if game["double_punishment"] else 1
            double = game["double_punishment"]
            game["pending_shots"] += shot_count
            sources = []
            if game["shot_sources"]:
                sources = game["shot_sources"].split(", ")
            sources.append(f"{shot_count} from flip")
            game["shot_sources"] = ", ".join(sources)
            game["double_punishment"] = False

    return {
        "call": call,
        "result": result,
        "won": won,
        "shielded": shielded,
        "double": double,
        "multiplier": multiplier,
        "net": net if won else 0,
        "bet": bet,
    }


def _run_witnesses(game):
    friends = game["friends"]
    results = []
    bs_count = 0
    for f in friends:
        called_bs = random.random() < f["bs_tendency"]
        results.append({"name": f["name"], "bs": called_bs})
        if called_bs:
            bs_count += 1
    penalty = bs_count >= 2
    if penalty:
        game["pending_shots"] += 1
        game["disputed_shots"] += 1
        if game["shot_sources"]:
            game["shot_sources"] += ", 1 from BS penalty"
        else:
            game["shot_sources"] = "1 from BS penalty"
    return results, penalty


@login_required
def coin_flip(request):
    game = _init_game(request.session)
    last_result = None
    challenge_result = None
    witness_results = None
    bs_penalty = False

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "flip_1" and game["tokens"] >= 1 and game["pending_shots"] == 0:
            last_result = _do_flip(game, 1)

        elif action == "flip_2" and game["tokens"] >= 2 and game["pending_shots"] == 0:
            last_result = _do_flip(game, 2)

        elif action == "all_in" and game["tokens"] >= 1 and game["pending_shots"] == 0:
            last_result = _do_flip(game, game["tokens"])

        elif action == "confirm_shots":
            count = game["pending_shots"]
            game["pending_shots"] = 0
            game["confirmed_shots"] += count
            game["shot_sources"] = ""
            witness_results, bs_penalty = _run_witnesses(game)

        elif action == "log_drinks":
            try:
                extra = int(request.POST.get("extra_drinks", 0))
            except (ValueError, TypeError):
                extra = 0
            if extra > 0:
                old_total = game["total_drinks"]
                game["total_drinks"] += extra
                old_tokens = _tokens_for_drinks(old_total)
                new_tokens = _tokens_for_drinks(game["total_drinks"])
                bonus = new_tokens - old_tokens
                if bonus > 0:
                    game["tokens"] += bonus
                    game["lifetime_earned"] += bonus

        elif action == "challenge" and game["pending_shots"] == 0:
            target_name = request.POST.get("challenge_target", "")
            try:
                stake = int(request.POST.get("challenge_stake", 1))
            except (ValueError, TypeError):
                stake = 1

            friend = None
            for f in game["friends"]:
                if f["name"] == target_name:
                    friend = f
                    break

            if friend and stake >= 1 and stake <= game["tokens"] and stake <= friend["tokens"]:
                result = random.choice(["heads", "tails"])
                call = random.choice(["heads", "tails"])
                won = result == call

                if won:
                    game["tokens"] += stake
                    game["lifetime_earned"] += stake
                    friend["tokens"] -= stake
                    game["challenges_won"] += 1
                else:
                    game["tokens"] -= stake
                    game["lifetime_spent"] += stake
                    friend["tokens"] += stake
                    game["challenges_lost"] += 1
                    game["pending_shots"] += 1
                    game["shot_sources"] = "1 from challenge"

                challenge_result = {
                    "opponent": friend["name"],
                    "result": result,
                    "won": won,
                    "stake": stake,
                }

        elif action == "shop_buy" and game["pending_shots"] == 0:
            item_key = request.POST.get("shop_item", "")
            target_name = request.POST.get("shop_target", "")

            item = None
            for si in COIN_SHOP_ITEMS:
                if si["key"] == item_key:
                    item = si
                    break

            friend = None
            for f in game["friends"]:
                if f["name"] == target_name:
                    friend = f
                    break

            if item and game["tokens"] >= item["cost"]:
                if item["needs_target"] and not friend:
                    pass
                else:
                    game["tokens"] -= item["cost"]
                    game["lifetime_spent"] += item["cost"]

                    if item_key == "force_shot":
                        friend["shots_owed"] += 1
                    elif item_key == "streak_breaker":
                        friend["streak"] = 0
                    elif item_key == "double_punishment":
                        friend["double_punishment"] = True
                    elif item_key == "shield":
                        game["has_shield"] = True
                    elif item_key == "token_heist":
                        stolen = min(2, friend["tokens"])
                        friend["tokens"] -= stolen
                        game["tokens"] += stolen
                        game["lifetime_earned"] += stolen

        request.session.modified = True

    win_rate = round(game["wins"] / game["total_flips"] * 100) if game["total_flips"] else 0

    context = {
        "game": {
            **game,
            "streak_multiplier": _streak_multiplier(game["streak"]),
            "win_rate": win_rate,
        },
        "game_name": request.user.username,
        "friends": game["friends"],
        "shop_items": COIN_SHOP_ITEMS,
        "last_result": last_result,
        "challenge_result": challenge_result,
        "witness_results": witness_results,
        "bs_penalty": bs_penalty,
    }
    return render(request, "accounts/coin_flip.html", context)


@login_required
def coin_flip_reset(request):
    if "coin_game" in request.session:
        del request.session["coin_game"]
    return redirect("coin_flip")

