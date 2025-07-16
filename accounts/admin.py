
from django.contrib import admin
from .models import Profile, FriendRequest, Post, DailyLog

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'xp', 'rank')
    search_fields = ('user__username', 'display_name')
    readonly_fields = ('xp', 'rank')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'display_name', 'xp', 'rank'),
        }),
        ('Alcohol Consumption', {
            'classes': ('collapse',),
            'fields': ('beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila'),
        }),
        ('Extras', {
            'classes': ('collapse',),
            'fields': ('shotguns', 'snorkels', 'thrown_up'),
        }),
        ('Social', {
            'classes': ('collapse',),
            'fields': ('friends',),
        }),
    )


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'date', 'xp')
    list_filter = ('date',)
    search_fields = ('profile__user__username',)
    readonly_fields = ('xp',)
    
    fieldsets = (
        (None, {
            'fields': ('profile', 'date', 'xp'),
        }),
        ('Drink Log', {
            'classes': ('collapse',),
            'fields': ('beer', 'floco', 'rum', 'whiskey', 'vodka', 'tequila'),
        }),
        ('Actions & Penalties', {
            'classes': ('collapse',),
            'fields': ('shotguns', 'snorkels', 'thrown_up'),
        }),
    )


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'accepted', 'created_at')
    list_filter = ('accepted', 'created_at')
    search_fields = ('from_user__user__username', 'to_user__user__username')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'content')
    search_fields = ('user__user__username', 'content')
    list_filter = ('created_at',)
