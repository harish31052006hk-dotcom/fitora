from django.contrib import admin
from .models import FoodEntry

@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'meal_category', 'food_name', 'serving_amount', 'serving_unit', 'calories')
    list_filter = ('meal_category', 'date')
    search_fields = ('food_name', 'user__username')
