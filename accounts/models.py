from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from achievements.models import Achievement
from datetime import timedelta, date
from django.utils import timezone


def current_log_date():
    """
    Returns the effective log date for Arizona (America/Phoenix timezone).
    Days run from 4 AM to 4 AM (adjusts the date if current time is between midnight-4 AM)
    """
    now = timezone.localtime(timezone.now())
    if now.hour < 4:
        return (now - timedelta(days=1)).date()
    return now.date()


# ─────────────────────────────────────────────
# RANK TABLES
# ─────────────────────────────────────────────

# Monthly — resets every 1st of the month, only that month's XP counts
MONTHLY_RANKS = [
    (0,    'Bronze'),
    (200,  'Silver'),
    (500,  'Gold'),
    (1000, 'Platinum'),
    (2000, 'Diamond'),
    (3000, 'Steeze'),
]

# Yearly — Jan 1 → Dec 31, higher thresholds
YEARLY_RANKS = [
    (0,     'Bronze'),
    (800,   'Silver'),
    (2000,  'Gold'),
    (5000,  'Platinum'),
    (12000, 'Diamond'),
    (25000, 'Steeze'),
]

# Lifetime — all-time XP, sub-ranks within each tier
LIFETIME_RANKS = [
    (0,      'Bronze 1'),
    (400,    'Bronze 2'),
    (800,    'Bronze 3'),
    (1500,   'Silver 1'),
    (2500,   'Silver 2'),
    (4000,   'Silver 3'),
    (6500,   'Gold 1'),
    (10000,  'Gold 2'),
    (15000,  'Gold 3'),
    (22000,  'Platinum 1'),
    (32000,  'Platinum 2'),
    (45000,  'Platinum 3'),
    (62000,  'Diamond 1'),
    (82000,  'Diamond 2'),
    (105000, 'Diamond 3'),
    (135000, 'Steeze 1'),
    (170000, 'Steeze 2'),
    (210000, 'Steeze 3'),
]


def _rank_from_xp(xp, rank_table):
    """Walk the table and return the highest matching rank label."""
    result = rank_table[0][1]
    for threshold, label in rank_table:
        if xp >= threshold:
            result = label
        else:
            break
    return result


def _next_threshold(xp, rank_table):
    """Returns the XP needed to reach the next rank, or None if maxed."""
    for threshold, label in rank_table:
        if xp < threshold:
            return threshold
    return None


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(
        max_length=15,
        default='User',
        help_text="Display name (letters only, max 15 characters)"
    )

    # Lifetime drink totals
    beer      = models.IntegerField(default=0, help_text="Number of Beers/Seltzers drank (17 ml alcohol per beer)")
    floco     = models.IntegerField(default=0, help_text="Number of Flocos (43 ml alcohol per shot)")
    rum       = models.IntegerField(default=0, help_text="Number of rum shots (9 ml alcohol per shot)")
    whiskey   = models.IntegerField(default=0, help_text="Number of whiskey shots (14 ml alcohol per shot)")
    vodka     = models.IntegerField(default=0, help_text="Number of vodka shots (18 ml alcohol per shot)")
    tequila   = models.IntegerField(default=0, help_text="Number of tequila shots (23 ml alcohol per shot)")
    shotguns  = models.IntegerField(default=0, help_text="Number of shotguns")
    snorkels  = models.IntegerField(default=0, help_text="Number of snorkels")
    thrown_up = models.IntegerField(default=0, help_text="Times thrown up")
    xp        = models.IntegerField(default=0, help_text="Lifetime XP")
    tokens    = models.IntegerField(default=0, help_text="Available token balance")

    # Rank fields
    rank         = models.CharField(max_length=50, default='Bronze 1', help_text="Lifetime sub-rank")
    monthly_rank = models.CharField(max_length=50, default='Bronze',   help_text="Current month rank (resets 1st of each month)")
    yearly_rank  = models.CharField(max_length=50, default='Bronze',   help_text="Current calendar year rank (resets Jan 1)")

    # Friends
    friends = models.ManyToManyField('self', symmetrical=False, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def post_count(self):
        from .models import Post
        return Post.objects.filter(user=self).count()

    # ── alcohol / XP math ────────────────────

    def calculate_alcohol_drank(self):
        """Calculate total alcohol consumed in milliliters (ml)"""
        return (
            (self.beer    * 17) +
            (self.floco   * 43) +
            (self.rum     *  9) +
            (self.whiskey * 14) +
            (self.vodka   * 18) +
            (self.tequila * 23)
        )

    def calculate_xp(self):
        """Calculate lifetime XP with bonuses and penalties"""
        alcohol_xp = self.calculate_alcohol_drank() * 0.75
        bonus_xp   = (self.shotguns * 5) + (self.snorkels * 15)
        penalties  = self.thrown_up * 40
        return max(round(alcohol_xp + bonus_xp - penalties, 2), 0)

    # ── XP slices from DailyLog ──────────────

    def _xp_from_logs(self, date_from, date_to):
        """Sum XP from DailyLog entries between two dates (inclusive)."""
        qs = self.daily_logs.filter(date__gte=date_from, date__lte=date_to)
        return sum(log.calculate_xp() for log in qs)

    def get_current_month_xp(self):
        """XP earned only within the current calendar month."""
        now = timezone.localtime(timezone.now())
        first = date(now.year, now.month, 1)
        if now.month == 12:
            last = date(now.year, 12, 31)
        else:
            last = date(now.year, now.month + 1, 1) - timedelta(days=1)
        return self._xp_from_logs(first, last)

    def get_yearly_xp(self):
        """XP earned Jan 1 → Dec 31 of the current calendar year."""
        now = timezone.localtime(timezone.now())
        return self._xp_from_logs(date(now.year, 1, 1), date(now.year, 12, 31))

    # ── rank update ──────────────────────────

    def update_rank(self):
        """Recompute all three rank fields."""
        self.rank         = _rank_from_xp(int(self.xp), LIFETIME_RANKS)
        self.yearly_rank  = _rank_from_xp(int(self.get_yearly_xp()), YEARLY_RANKS)
        self.monthly_rank = _rank_from_xp(int(self.get_current_month_xp()), MONTHLY_RANKS)

    def save(self, *args, **kwargs):
        """Auto-calculate XP and all ranks before saving."""
        self.xp = self.calculate_xp()
        self.update_rank()
        super().save(*args, **kwargs)

    # ── lifetime progress helpers ────────────

    @property
    def xp_to_next_level(self):
        """XP threshold of the next lifetime rank, or None if maxed."""
        return _next_threshold(int(self.xp), LIFETIME_RANKS)

    @property
    def xp_percentage(self):
        """Progress to next lifetime rank as 0-100."""
        if self.rank == 'Steeze 3':
            return 100
        next_xp = self.xp_to_next_level
        if not next_xp:
            return 100
        current_floor = 0
        for threshold, _ in LIFETIME_RANKS:
            if self.xp >= threshold:
                current_floor = threshold
            else:
                break
        span = next_xp - current_floor
        if span <= 0:
            return 100
        return min(100, int(((self.xp - current_floor) / span) * 100))

    def check_achievements(self):
        """Check each Achievement to see if this profile qualifies."""
        earned = []
        for achievement in Achievement.objects.all():
            if achievement.qualifies(self):
                earned.append(achievement)
        return earned


# ─────────────────────────────────────────────
# MONTHLY RANK HISTORY
# ─────────────────────────────────────────────

class MonthlyRankHistory(models.Model):
    """Snapshot of a user's rank at the end of each calendar month."""
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='monthly_rank_history'
    )
    year  = models.IntegerField()
    month = models.IntegerField()  # 1-12
    rank  = models.CharField(max_length=50)
    xp    = models.IntegerField(default=0)

    class Meta:
        unique_together = ('profile', 'year', 'month')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.profile.user.username} — {self.year}/{self.month:02d}: {self.rank}"


# ─────────────────────────────────────────────
# FRIEND REQUEST
# ─────────────────────────────────────────────

class FriendRequest(models.Model):
    from_user  = models.ForeignKey(Profile, related_name='sent_friend_requests',     on_delete=models.CASCADE)
    to_user    = models.ForeignKey(Profile, related_name='received_friend_requests', on_delete=models.CASCADE)
    accepted   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_user', 'to_user']

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({'Accepted' if self.accepted else 'Pending'})"

    def accept(self):
        """Accept friend request and establish mutual friendship"""
        self.to_user.friends.add(self.from_user)
        self.from_user.friends.add(self.to_user)
        self.accepted = True
        self.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# ─────────────────────────────────────────────
# POST
# ─────────────────────────────────────────────

class Post(models.Model):
    user       = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content    = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    likes      = models.ManyToManyField(Profile, related_name='liked_posts', blank=True)

    def __str__(self):
        return f"{self.user.user.username}: {self.content[:20]}..."

    class Meta:
        ordering = ['-created_at']


# ─────────────────────────────────────────────
# DAILY LOG
# ─────────────────────────────────────────────

class DailyLog(models.Model):
    profile   = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="daily_logs")
    date      = models.DateField(help_text="Log date (4 AM to 4 AM)", default=current_log_date)

    beer      = models.PositiveIntegerField(default=0)
    floco     = models.PositiveIntegerField(default=0)
    rum       = models.PositiveIntegerField(default=0)
    whiskey   = models.PositiveIntegerField(default=0)
    vodka     = models.PositiveIntegerField(default=0)
    tequila   = models.PositiveIntegerField(default=0)
    shotguns  = models.PositiveIntegerField(default=0)
    snorkels  = models.PositiveIntegerField(default=0)
    thrown_up = models.PositiveIntegerField(default=0)
    xp        = models.IntegerField(default=0)

    class Meta:
        unique_together = ("profile", "date")
        ordering = ['-date']

    def __str__(self):
        return f"{self.profile.user.username} - {self.date}"

    def calculate_alcohol_drank(self):
        return (
            (self.beer    * 17) +
            (self.floco   * 43) +
            (self.rum     *  9) +
            (self.whiskey * 14) +
            (self.vodka   * 18) +
            (self.tequila * 23)
        )

    def calculate_xp(self):
        alcohol_xp = self.calculate_alcohol_drank() * 0.75
        bonus_xp   = (self.shotguns * 5) + (self.snorkels * 15)
        penalties  = self.thrown_up * 40
        return max(round(alcohol_xp + bonus_xp - penalties, 2), 0)

    def update_xp(self):
        self.xp = self.calculate_xp()
        self.save()


# ─────────────────────────────────────────────
# TOKEN TRANSACTION
# ─────────────────────────────────────────────

class TokenTransaction(models.Model):
    EARN = 'earn'
    SPEND = 'spend'
    TYPE_CHOICES = [
        (EARN, 'Earn'),
        (SPEND, 'Spend'),
    ]

    profile       = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='token_transactions')
    type          = models.CharField(max_length=5, choices=TYPE_CHOICES)
    amount        = models.PositiveIntegerField()
    reason        = models.CharField(max_length=255)
    balance_after = models.IntegerField(help_text="Token balance after this transaction")
    competition_id_ref = models.IntegerField(null=True, blank=True, help_text="Optional competition ID this relates to")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.type == self.EARN else '-'
        return f"{self.profile.user.username} {sign}{self.amount} ({self.reason})"


# ─────────────────────────────────────────────
# TOKEN HELPERS
# ─────────────────────────────────────────────

def add_tokens(profile, amount, reason, competition_id_ref=None):
    if amount <= 0:
        raise ValueError("amount must be positive")
    profile.tokens += amount
    profile.save(update_fields=['tokens'])
    return TokenTransaction.objects.create(
        profile=profile,
        type=TokenTransaction.EARN,
        amount=amount,
        reason=reason,
        balance_after=profile.tokens,
        competition_id_ref=competition_id_ref,
    )


def spend_tokens(profile, amount, reason, competition_id_ref=None):
    if amount <= 0:
        raise ValueError("amount must be positive")
    if profile.tokens < amount:
        raise ValueError("insufficient tokens")
    profile.tokens -= amount
    profile.save(update_fields=['tokens'])
    return TokenTransaction.objects.create(
        profile=profile,
        type=TokenTransaction.SPEND,
        amount=amount,
        reason=reason,
        balance_after=profile.tokens,
        competition_id_ref=competition_id_ref,
    )
