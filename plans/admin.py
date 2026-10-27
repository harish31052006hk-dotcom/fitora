from django.contrib import admin
from .models import WeeklyPlan


@admin.register(WeeklyPlan)
class WeeklyPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'week_start', 'generation_source', 'updated_at')
    list_filter = ('generation_source', 'week_start')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
