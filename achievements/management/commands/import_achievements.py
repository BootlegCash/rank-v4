import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from achievements.models import Achievement

class Command(BaseCommand):
    help = "Import achievements from a JSON file"

    def handle(self, *args, **options):
        # Define the path to your JSON file. Adjust if necessary.
        file_path = os.path.join(settings.BASE_DIR, 'achievements', 'data', 'achievements.json')
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Open with explicit UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for achievement_data in data:
            code = achievement_data.get('code')
            name = achievement_data.get('name')
            description = achievement_data.get('description', '')
            points = achievement_data.get('points', 0)
            # Create or update the achievement based on the unique code.
            achievement, created = Achievement.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'points': points
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created achievement: {code}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated achievement: {code}"))

        self.stdout.write(self.style.SUCCESS("Achievement import completed!"))
