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

from achievements.models import Achievement
from .forms import RegistrationForm, StatsUpdateForm, SendFriendRequestForm, PostForm, DailyLogForm
from .models import Profile, FriendRequest, Post, DailyLog, current_log_date

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



