import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
django.setup()

from accounts.models import Profile

updated = 0
for profile in Profile.objects.all():
    profile.save()  # triggers update_rank() automatically
    updated += 1
    print(f"Fixed {profile.user.username}: {profile.rank} | monthly: {profile.monthly_rank} | yearly: {profile.yearly_rank}")

print(f"\nDone — updated {updated} profiles.")