from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_calorie_goal', 'daily_protein_goal', 'daily_carbs_goal', 'daily_fat_goal', 'current_weight')
    search_fields = ('user__username', 'user__email')
