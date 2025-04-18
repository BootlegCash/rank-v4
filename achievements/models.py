from django.db import models
from .requirements import ACHIEVEMENT_REQUIREMENTS

class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True, default='')  # New icon field for emoji or icon strings.
    points = models.IntegerField(default=0)
    profiles = models.ManyToManyField('accounts.Profile', related_name="earned_achievements", blank=True)

    def qualifies(self, profile):
        """Checks if the profile qualifies for this achievement using the registered requirement function."""
        requirement_func = ACHIEVEMENT_REQUIREMENTS.get(self.code)
        if requirement_func:
            return requirement_func(profile)
        return False

    def __str__(self):
        return self.name
