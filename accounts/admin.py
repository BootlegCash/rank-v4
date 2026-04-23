from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db.models import Sum, Count
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Profile, DailyLog


DRINK_FIELDS = ["beer", "floco", "rum", "whiskey", "vodka", "tequila"]


class DailyLogInline(admin.TabularInline):
    model = DailyLog
    extra = 0
    fields = (
        "date", "beer", "floco", "rum", "whiskey", "vodka", "tequila",
        "shotguns", "snorkels", "thrown_up", "xp"
    )
    readonly_fields = fields
    ordering = ("-date",)
    show_change_link = False
    can_delete = False
    max_num = 10


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "rank_badge",
        "xp",
        "favorite_drink",
        "total_drinks",
        "total_alcohol_ml",
        "shotguns",
        "snorkels",
        "thrown_up",
        "view_stats",
    )
    search_fields = ("user__username", "display_name", "rank")
    list_filter = ("rank",)
    ordering = ("-xp",)
    inlines = [DailyLogInline]

    readonly_fields = (
        "xp",
        "rank_badge_large",
        "xp_progress_bar",
        "favorite_drink",
        "total_drinks",
        "total_alcohol_ml",
        "profile_summary_card",
        "drink_breakdown_card",
    )

    fieldsets = (
        ("👤 User", {
            "fields": ("user", "display_name"),
        }),
        ("🏆 Rank & XP", {
            "fields": ("rank", "xp", "rank_badge_large", "xp_progress_bar"),
        }),
        ("📊 Quick Statistics", {
            "fields": (
                "favorite_drink",
                "total_drinks",
                "total_alcohol_ml",
                "profile_summary_card",
            ),
        }),
        ("🍻 Drink Totals", {
            "fields": (
                "beer", "floco", "rum", "whiskey", "vodka", "tequila",
                "shotguns", "snorkels", "thrown_up",
                "drink_breakdown_card",
            ),
            "description": "Cumulative lifetime stats for this profile.",
        }),
    )

    change_list_template = "admin/accounts/profile/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "stats/",
                self.admin_site.admin_view(self.stats_dashboard_view),
                name="accounts_profile_stats",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["stats_dashboard_url"] = reverse("admin:accounts_profile_stats")
        return super().changelist_view(request, extra_context=extra_context)

    def stats_dashboard_view(self, request):
        totals = Profile.objects.aggregate(
            total_profiles=Count("id"),
            beer_total=Sum("beer"),
            floco_total=Sum("floco"),
            rum_total=Sum("rum"),
            whiskey_total=Sum("whiskey"),
            vodka_total=Sum("vodka"),
            tequila_total=Sum("tequila"),
            shotguns_total=Sum("shotguns"),
            snorkels_total=Sum("snorkels"),
            thrown_up_total=Sum("thrown_up"),
            total_xp=Sum("xp"),
        )

        rank_counts_qs = Profile.objects.values("rank").annotate(count=Count("id"))
        rank_counts = {row["rank"]: row["count"] for row in rank_counts_qs}
        ordered_ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Steez"]
        rank_labels = ordered_ranks
        rank_values = [rank_counts.get(rank, 0) for rank in ordered_ranks]

        drink_totals = {
            "Beer": totals.get("beer_total") or 0,
            "Floco": totals.get("floco_total") or 0,
            "Rum": totals.get("rum_total") or 0,
            "Whiskey": totals.get("whiskey_total") or 0,
            "Vodka": totals.get("vodka_total") or 0,
            "Tequila": totals.get("tequila_total") or 0,
        }

        favorite_drink_name = max(drink_totals, key=drink_totals.get) if drink_totals else "N/A"

        context = {
            **self.admin_site.each_context(request),
            "title": "Profile Statistics Dashboard",
            "opts": self.model._meta,
            "total_profiles": totals.get("total_profiles") or 0,
            "total_xp": totals.get("total_xp") or 0,
            "total_shotguns": totals.get("shotguns_total") or 0,
            "total_snorkels": totals.get("snorkels_total") or 0,
            "total_thrown_up": totals.get("thrown_up_total") or 0,
            "favorite_drink_name": favorite_drink_name,
            "drink_labels": list(drink_totals.keys()),
            "drink_values": list(drink_totals.values()),
            "rank_labels": rank_labels,
            "rank_values": rank_values,
        }
        return TemplateResponse(request, "admin/accounts/profile/stats.html", context)

    def rank_badge(self, obj):
        emoji_map = {
            "Bronze": "🥉",
            "Silver": "🥈",
            "Gold": "🥇",
            "Platinum": "🔘",
            "Diamond": "💎",
            "Steez": "👑",
        }
        emoji = emoji_map.get(obj.rank, "🏅")
        return format_html(
            '<span style="font-weight:700;">{} {}</span>',
            emoji,
            obj.rank,
        )
    rank_badge.short_description = "Rank"

    def rank_badge_large(self, obj):
        emoji_map = {
            "Bronze": "🥉",
            "Silver": "🥈",
            "Gold": "🥇",
            "Platinum": "🔘",
            "Diamond": "💎",
            "Steez": "👑",
        }
        emoji = emoji_map.get(obj.rank, "🏅")
        return format_html(
            """
            <div style="
                padding:14px 16px;
                border-radius:14px;
                background:linear-gradient(135deg,#111827,#1f2937);
                color:white;
                display:inline-block;
                min-width:220px;
                box-shadow:0 8px 24px rgba(0,0,0,.18);
            ">
                <div style="font-size:28px; line-height:1;">{}</div>
                <div style="font-size:18px; font-weight:800; margin-top:6px;">{}</div>
            </div>
            """,
            emoji,
            obj.rank,
        )
    rank_badge_large.short_description = "Rank Preview"

    def xp_progress_bar(self, obj):
        pct = obj.xp_percentage if hasattr(obj, "xp_percentage") else 0
        next_xp = obj.xp_to_next_level if hasattr(obj, "xp_to_next_level") else None
        next_text = "MAX RANK" if obj.rank == "Steez" else f"{next_xp} XP to next rank"
        return format_html(
            """
            <div style="min-width:320px;">
                <div style="
                    height:16px;
                    background:#1f2937;
                    border-radius:999px;
                    overflow:hidden;
                    box-shadow:inset 0 1px 3px rgba(0,0,0,.35);
                ">
                    <div style="
                        width:{}%;
                        height:100%;
                        background:linear-gradient(90deg,#06b6d4,#3b82f6,#a855f7);
                    "></div>
                </div>
                <div style="margin-top:8px; font-weight:700;">{} XP</div>
                <div style="font-size:12px; color:#6b7280;">{}</div>
            </div>
            """,
            pct,
            obj.xp,
            next_text,
        )
    xp_progress_bar.short_description = "XP Progress"

    def total_drinks(self, obj):
        return sum(getattr(obj, field, 0) for field in DRINK_FIELDS)
    total_drinks.short_description = "Total Drinks"

    def total_alcohol_ml(self, obj):
        return obj.calculate_alcohol_drank()
    total_alcohol_ml.short_description = "Alcohol (ml)"

    def favorite_drink(self, obj):
        drink_map = {
            "beer": ("🍺", "Beer"),
            "floco": ("🥃", "Floco"),
            "rum": ("🍹", "Rum"),
            "whiskey": ("🥃", "Whiskey"),
            "vodka": ("🍸", "Vodka"),
            "tequila": ("🍶", "Tequila"),
        }
        best_key = max(DRINK_FIELDS, key=lambda field: getattr(obj, field, 0))
        best_value = getattr(obj, best_key, 0)

        if best_value == 0:
            return "No drinks logged"

        emoji, label = drink_map[best_key]
        return f"{emoji} {label} ({best_value})"
    favorite_drink.short_description = "Favorite Drink"

    def profile_summary_card(self, obj):
        return format_html(
            """
            <div style="
                display:grid;
                grid-template-columns:repeat(auto-fit, minmax(160px, 1fr));
                gap:12px;
                max-width:900px;
            ">
                <div style="padding:14px;border-radius:14px;background:#0f172a;color:#fff;">
                    <div style="font-size:12px;opacity:.75;">Favorite Drink</div>
                    <div style="font-size:20px;font-weight:800;margin-top:6px;">{}</div>
                </div>
                <div style="padding:14px;border-radius:14px;background:#0f172a;color:#fff;">
                    <div style="font-size:12px;opacity:.75;">Total Drinks</div>
                    <div style="font-size:20px;font-weight:800;margin-top:6px;">{}</div>
                </div>
                <div style="padding:14px;border-radius:14px;background:#0f172a;color:#fff;">
                    <div style="font-size:12px;opacity:.75;">Alcohol Consumed</div>
                    <div style="font-size:20px;font-weight:800;margin-top:6px;">{} ml</div>
                </div>
                <div style="padding:14px;border-radius:14px;background:#0f172a;color:#fff;">
                    <div style="font-size:12px;opacity:.75;">Performance</div>
                    <div style="font-size:20px;font-weight:800;margin-top:6px;">💥 {} | 🤿 {} | 🤢 {}</div>
                </div>
            </div>
            """,
            self.favorite_drink(obj),
            self.total_drinks(obj),
            self.total_alcohol_ml(obj),
            obj.shotguns,
            obj.snorkels,
            obj.thrown_up,
        )
    profile_summary_card.short_description = "Stats Cards"

    def drink_breakdown_card(self, obj):
        drinks = [
            ("🍺 Beer", obj.beer),
            ("🥃 Floco", obj.floco),
            ("🍹 Rum", obj.rum),
            ("🥃 Whiskey", obj.whiskey),
            ("🍸 Vodka", obj.vodka),
            ("🍶 Tequila", obj.tequila),
        ]
        total = max(sum(v for _, v in drinks), 1)

        rows = []
        for label, value in drinks:
            pct = round((value / total) * 100, 1)
            rows.append(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;font-weight:600;">
                        <span>{label}</span>
                        <span>{value}</span>
                    </div>
                    <div style="height:10px;background:#1f2937;border-radius:999px;overflow:hidden;margin-top:4px;">
                        <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#06b6d4,#a855f7);"></div>
                    </div>
                </div>
            """)

        return format_html(
            """
            <div style="
                max-width:700px;
                background:#111827;
                color:white;
                border-radius:16px;
                padding:16px;
                box-shadow:0 8px 24px rgba(0,0,0,.15);
            ">
                <div style="font-size:16px;font-weight:800;margin-bottom:12px;">Drink Breakdown</div>
                {}
            </div>
            """,
            format_html("".join(rows)),
        )
    drink_breakdown_card.short_description = "Drink Breakdown"

    def view_stats(self, obj):
        url = reverse("admin:accounts_profile_change", args=[obj.pk])
        return format_html('<a class="button" href="{}">Open</a>', url)
    view_stats.short_description = "Profile Link"


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("view_profile_link",)

    def view_profile_link(self, obj):
        try:
            url = reverse("admin:accounts_profile_change", args=[obj.profile.id])
            return format_html('<a href="{}">View Profile</a>', url)
        except Profile.DoesNotExist:
            return "No profile"
    view_profile_link.short_description = "Profile"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)