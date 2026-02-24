from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re

from .models import Profile

# If you have a Post model in accounts/models.py, keep this import.
# If you DON'T have Post, comment this line AND the PostForm class below.
try:
    from .models import Post
except Exception:
    Post = None


# ============================
# REGISTRATION FORM (EMAIL ADDED)
# ============================

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    display_name = forms.CharField(
        max_length=15,
        required=True,
        help_text="Display name must contain only letters and be 15 characters or fewer."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'display_name', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').lower()
        if len(username) > 15:
            raise forms.ValidationError("Username must be 15 characters or fewer.")
        if not re.fullmatch(r'[a-z0-9]+', username):
            raise forms.ValidationError("Username can only contain lowercase letters and numbers.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("That email is already in use.")
        return email

    def clean_display_name(self):
        display_name = self.cleaned_data.get('display_name', '')
        if len(display_name) > 15:
            raise forms.ValidationError("Display name must be 15 characters or fewer.")
        if not re.fullmatch(r'[A-Za-z]+', display_name):
            raise forms.ValidationError("Display name can only contain letters.")
        return display_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()

        # Profile auto-created via signal in your models
        user.profile.display_name = self.cleaned_data.get('display_name')
        user.profile.save()
        return user


# ============================
# PROFILE STATS UPDATE FORM
# (FIXED field names)
# ============================

class StatsUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'beer',
            'floco',
            'rum',
            'whiskey',
            'vodka',
            'tequila',
            'shotguns',
            'snorkels',
            'thrown_up',
        ]


# ============================
# FRIEND REQUEST FORM
# ============================

class SendFriendRequestForm(forms.Form):
    username = forms.CharField(max_length=15)

    def clean_username(self):
        username = self.cleaned_data.get('username', '').lower()
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError("User does not exist.")
        return username


# ============================
# POST FORM (ONLY if Post model exists)
# ============================

if Post is not None:
    class PostForm(forms.ModelForm):
        class Meta:
            model = Post
            fields = ['content']

        content = forms.CharField(
            max_length=280,
            widget=forms.Textarea(attrs={
                'rows': 3,
                'placeholder': "What’s happening tonight?"
            })
        )


# ============================
# DAILY LOG FORM
# (If you have a DailyLog model, tell me and I'll switch this to use it.)
# For now, this matches your current Profile fields so it won't crash.
# ============================

class DailyLogForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'beer',
            'floco',
            'rum',
            'whiskey',
            'vodka',
            'tequila',
            'shotguns',
            'snorkels',
            'thrown_up',
        ]