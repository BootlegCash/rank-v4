import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from accounts.models import Profile

for profile in Profile.objects.all():
    print(f"\nUser: {profile.user.username}")
    print(f"  Lifetime XP:    {profile.xp}")
    print(f"  Lifetime rank:  {profile.rank}")
    print(f"  Monthly XP:     {profile.get_current_month_xp()}")
    print(f"  Monthly rank:   {profile.monthly_rank}")
    print(f"  Yearly XP:      {profile.get_yearly_xp()}")
    print(f"  Yearly rank:    {profile.yearly_rank}")
    print(f"  XP to next:     {profile.xp_to_next_level}")
    print(f"  XP %:           {profile.xp_percentage}%")