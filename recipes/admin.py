from django.contrib import admin
from .models import Recipe, RecipeIngredient, SavedMeal, SavedMealItem

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'servings', 'is_favorite_meal', 'updated_at')
    list_filter = ('is_favorite_meal',)
    search_fields = ('name', 'user__username')
    inlines = [RecipeIngredientInline]

class SavedMealItemInline(admin.TabularInline):
    model = SavedMealItem
    extra = 1

@admin.register(SavedMeal)
class SavedMealAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'total_calories', 'created_at')
    search_fields = ('name', 'user__username')
    inlines = [SavedMealItemInline]
