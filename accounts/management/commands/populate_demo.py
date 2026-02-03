import random
import string
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile, Post, DailyLog, current_log_date  # uses your models


FIRST_NAMES = [
    "Ryan","Amelia","Jake","Mason","Noah","Liam","Ethan","Aiden","Lucas","Logan",
    "Mia","Emma","Ava","Sofia","Chloe","Olivia","Grace","Zoe","Lily","Nora",
    "Alex","Jordan","Taylor","Casey","Riley","Cameron","Parker","Quinn","Blake"
]

POST_TEMPLATES = [
    "Pre-game energy is insane 🔥",
    "Ranked up tonight 😮‍💨",
    "Who’s trying to run it back this weekend?",
    "Shotgun count going crazy 💥",
    "Leaderboard check… I’m coming for #1 😈",
    "Hydrate, eat, pace. Then rank up 🍻",
    "After Hours vibes only 🌙✨",
]

def rand_username(prefix: str, n: int = 4) -> str:
    # Must be <= 15 chars and lowercase letters/numbers only (per your RegistrationForm)
    suffix = ''.join(random.choices(string.digits, k=n))
    base = (prefix.lower()[: (15 - len(suffix))]) + suffix
    base = ''.join(ch for ch in base if ch.isalnum()).lower()
    return base[:15]

def clamp_int(x, lo=0, hi=10_000):
    return max(lo, min(int(x), hi))


class Command(BaseCommand):
    help = "Populate the database with demo users, stats, friendships, posts, and daily logs."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=25, help="Number of fake users to create.")
        parser.add_argument("--days", type=int, default=7, help="How many past days of DailyLogs to create per user.")
        parser.add_argument("--hub-username", type=str, default="demo", help="Hub account username (<=15 chars).")
        parser.add_argument("--hub-password", type=str, default="DemoPass123!", help="Hub account password.")
        parser.add_argument("--reset", action="store_true", help="Delete existing demo users/posts/logs created by this command.")
        parser.add_argument("--mutual-network", action="store_true", help="Also add friends between fake users (denser feed/leaderboard).")
        parser.add_argument("--posts-per-user", type=int, default=2, help="How many posts each fake user makes.")
        parser.add_argument("--likes-per-post", type=int, default=3, help="How many random likes per post.")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable data.")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        users_n = max(0, int(opts["users"]))
        days_n = max(0, int(opts["days"]))
        hub_username = opts["hub_username"][:15].lower()
        hub_password = opts["hub_password"]
        reset = opts["reset"]
        mutual_network = opts["mutual_network"]
        posts_per_user = max(0, int(opts["posts_per_user"]))
        likes_per_post = max(0, int(opts["likes_per_post"]))

        # Tag so we can safely reset only what we created
        DEMO_TAG_PREFIX = "demo_"
        created_usernames = []

        if reset:
            # Delete users starting with demo_ OR the hub username
            qs = User.objects.filter(username__startswith=DEMO_TAG_PREFIX) | User.objects.filter(username=hub_username)
            # Cascade will remove Profile, Posts, DailyLogs via FK relations
            count = qs.count()
            qs.delete()
            self.stdout.write(self.style.WARNING(f"Reset: deleted {count} demo users (and related data)."))

        # Create hub account
        hub_user, created = User.objects.get_or_create(username=hub_username)
        if created:
            hub_user.set_password(hub_password)
            hub_user.save()
        else:
            # ensure password is what you want for screenshots
            hub_user.set_password(hub_password)
            hub_user.save()

        hub_profile = hub_user.profile  # auto-created via post_save signal
        # Give hub a strong-looking profile so screenshots look good
        hub_profile.beer = 60
        hub_profile.floco = 8
        hub_profile.rum = 20
        hub_profile.whiskey = 30
        hub_profile.vodka = 25
        hub_profile.tequila = 18
        hub_profile.shotguns = 12
        hub_profile.snorkels = 6
        hub_profile.thrown_up = 0
        hub_profile.save()  # recalculates xp + rank in save()

        # Display name is stored on profile in your RegistrationForm save()
        # (Not required for auth; safe to set directly)
        hub_profile.display_name = "Demo"
        hub_profile.save()

        self.stdout.write(self.style.SUCCESS(f"Hub account ready: {hub_username} / {hub_password}"))

        # Create fake users
        for i in range(users_n):
            name = random.choice(FIRST_NAMES)
            # prefix with demo_ so reset is safe
            uname = rand_username(DEMO_TAG_PREFIX + name, n=4)
            # Guarantee uniqueness if collisions
            while User.objects.filter(username=uname).exists():
                uname = rand_username(DEMO_TAG_PREFIX + name, n=4)

            u = User.objects.create_user(username=uname, password="DemoPass123!")
            created_usernames.append(uname)

            p = u.profile
            # Respect display_name constraint: letters only <=15
            display = ''.join(ch for ch in name if ch.isalpha())[:15] or "Player"
            p.display_name = display

            # Random but plausible stats
            p.beer = clamp_int(random.gauss(18, 12), 0, 80)
            p.floco = clamp_int(random.gauss(4, 4), 0, 20)
            p.rum = clamp_int(random.gauss(8, 8), 0, 40)
            p.whiskey = clamp_int(random.gauss(10, 10), 0, 50)
            p.vodka = clamp_int(random.gauss(9, 9), 0, 50)
            p.tequila = clamp_int(random.gauss(7, 8), 0, 50)
            p.shotguns = clamp_int(random.gauss(3, 3), 0, 25)
            p.snorkels = clamp_int(random.gauss(1, 2), 0, 15)
            p.thrown_up = clamp_int(random.choice([0,0,0,1,1,2]), 0, 10)
            p.save()

            # Make hub friends with this user (mutual)
            hub_profile.friends.add(p)
            p.friends.add(hub_profile)

        fake_profiles = list(Profile.objects.filter(user__username__in=created_usernames))
        self.stdout.write(self.style.SUCCESS(f"Created {len(fake_profiles)} demo users (password: DemoPass123!)."))

        # Optional: connect fake users to each other (denser leaderboard/feed)
        if mutual_network and len(fake_profiles) >= 3:
            for p in fake_profiles:
                # each user gets ~3-8 random friends among fake users
                k = random.randint(3, min(8, len(fake_profiles)-1))
                candidates = [x for x in fake_profiles if x.id != p.id]
                picks = random.sample(candidates, k=k)
                for other in picks:
                    p.friends.add(other)
                    other.friends.add(p)

        # Create DailyLogs for each fake user (and hub too)
        def make_daily_logs(profile: Profile, days: int):
            today = current_log_date()
            for d in range(days):
                day = today - timedelta(days=d)
                log, _ = DailyLog.objects.get_or_create(profile=profile, date=day)
                # Small daily increments
                log.beer = clamp_int(random.gauss(2, 2), 0, 10)
                log.floco = clamp_int(random.gauss(1, 1), 0, 5)
                log.rum = clamp_int(random.gauss(1, 2), 0, 8)
                log.whiskey = clamp_int(random.gauss(1, 2), 0, 8)
                log.vodka = clamp_int(random.gauss(1, 2), 0, 8)
                log.tequila = clamp_int(random.gauss(1, 2), 0, 8)
                log.shotguns = clamp_int(random.choice([0, 0, 1, 2]), 0, 5)
                log.snorkels = clamp_int(random.choice([0, 0, 0, 1]), 0, 3)
                log.thrown_up = clamp_int(random.choice([0, 0, 0, 0, 1]), 0, 2)
                log.xp = log.calculate_xp()
                log.save()

        make_daily_logs(hub_profile, days_n)
        for p in fake_profiles:
            make_daily_logs(p, days_n)

        # Create posts + likes
        all_profiles_for_likes = [hub_profile] + fake_profiles

        created_posts = 0
        for p in fake_profiles:
            for _ in range(posts_per_user):
                text = random.choice(POST_TEMPLATES)
                post = Post.objects.create(user=p, content=text)
                created_posts += 1

                # Likes
                likers = random.sample(
                    [x for x in all_profiles_for_likes if x.id != p.id],
                    k=min(likes_per_post, len(all_profiles_for_likes)-1)
                )
                for liker in likers:
                    post.likes.add(liker)

        # Hub posts too (so your feed looks alive when logged in as hub)
        for _ in range(max(1, posts_per_user)):
            post = Post.objects.create(user=hub_profile, content=random.choice(POST_TEMPLATES))
            created_posts += 1
            likers = random.sample(
                [x for x in all_profiles_for_likes if x.id != hub_profile.id],
                k=min(likes_per_post + 2, len(all_profiles_for_likes)-1)
            )
            for liker in likers:
                post.likes.add(liker)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Hub: {hub_username}. Users: {len(fake_profiles)}. Posts: {created_posts}. Days/logs: {days_n}."
        ))
