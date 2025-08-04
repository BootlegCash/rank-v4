from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # adjust this if your last migration isn’t 0014
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='display_name',
            field=models.CharField(
                max_length=15,
                default='User',
                help_text="Display name (letters only, max 15 characters)"
            ),
        ),
    ]
