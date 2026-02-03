from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile


# ---- Profile Admin ----
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'display_name',   # ✅ shows in list
        'rank',
        'xp',
        'beer',
        'floco',
        'rum',
        'whiskey',
        'vodka',
        'tequila',
        'shotguns',
        'snorkels',
        'thrown_up',
        'view_stats'
    )

    # ✅ allow searching by display name too
    search_fields = ('user__username', 'display_name', 'rank')
    list_filter = ('rank',)
    ordering = ('-xp',)

    # Group fields into nice sections
    fieldsets = (
        ('User Info', {
            # ✅ THIS is the key change
            'fields': ('user', 'display_name', 'rank', 'xp'),
        }),
        ('Drink Stats', {
            'fields': (
                'beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila',
                'shotguns', 'snorkels', 'thrown_up'
            ),
            'description': "Cumulative stats for all drinks logged.",
        }),
    )

    readonly_fields = ('xp',)  # Prevent editing XP manually

    def view_stats(self, obj):
        return format_html(
            '<a class="button" href="/admin/accounts/profile/{}/change/">View Profile</a>',
            obj.id
        )
    view_stats.short_description = 'Profile Link'


# ---- Extend User Admin to include Profile link ----
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('view_profile_link',)

    def view_profile_link(self, obj):
        try:
            return format_html(
                '<a href="/admin/accounts/profile/{}/change/">View Profile</a>',
                obj.profile.id
            )
        except Profile.DoesNotExist:
            return "No profile"
    view_profile_link.short_description = 'Profile'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
