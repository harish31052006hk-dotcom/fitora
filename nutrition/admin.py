from django.contrib import admin
from .models import FoodItem

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'serving_size', 'serving_unit', 'calories', 'protein', 'carbohydrates', 'fat', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('name', 'brand')
