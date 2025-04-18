from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Post
import re

class RegistrationForm(UserCreationForm):
    display_name = forms.CharField(
        max_length=15,
        required=True,
        help_text="Display name must contain only letters and be 15 characters or fewer."
    )

    class Meta:
        model = User
        fields = ['username', 'display_name', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').lower()
        if len(username) > 15:
            raise forms.ValidationError("Username must be 15 characters or fewer.")
        if not re.fullmatch(r'[a-z0-9]+', username):
            raise forms.ValidationError("Username can only contain lowercase letters and numbers.")
        return username

    def clean_display_name(self):
        display_name = self.cleaned_data.get('display_name', '')
        if len(display_name) > 15:
            raise forms.ValidationError("Display name must be 15 characters or fewer.")
        if not re.fullmatch(r'[A-Za-z]+', display_name):
            raise forms.ValidationError("Display name can only contain letters.")
        return display_name

    def save(self, commit=True):
        # Save the User instance first.
        user = super().save(commit)
        # Then update the profile (which is auto-created via your signal).
        user.profile.display_name = self.cleaned_data.get('display_name')
        user.profile.save()
        return user

class StatsUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vodka'].label = "vodka (40%)"
        self.fields['tequila'].label = "tequila (50%)"
        self.fields['whiskey'].label = "whiskey (30%)"
        self.fields['rum'].label = "rum (20%)"
        self.fields['floco'].label = "floco (13%) (12 oz)"
        self.fields['beer'].label = "beer/seltzer (5%) (12oz)"
        
        
        
    class Meta:
        model = Profile
        fields = [
            'beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila',
            'shotguns', 'snorkels', 'thrown_up'
        ]

class SendFriendRequestForm(forms.Form):
    username = forms.CharField(label="Friend's Username", max_length=150)

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': "What's happening in your night?",
                'maxlength': '280'
            })
        }

class DailyLogForm(forms.Form):
    beer = forms.IntegerField(min_value=0, initial=0, label="Beers/Seltzers")
    floco = forms.IntegerField(min_value=0, initial=0, label="Flocos")
    rum = forms.IntegerField(min_value=0, initial=0, label="Rum Shots")
    whiskey = forms.IntegerField(min_value=0, initial=0, label="Whiskey Shots")
    vodka = forms.IntegerField(min_value=0, initial=0, label="Vodka Shots")
    tequila = forms.IntegerField(min_value=0, initial=0, label="Tequila Shots")
    shotguns = forms.IntegerField(min_value=0, initial=0, label="Shotguns")
    snorkels = forms.IntegerField(min_value=0, initial=0, label="Snorkels")
    thrown_up = forms.IntegerField(min_value=0, initial=0, label="Times Thrown Up")
