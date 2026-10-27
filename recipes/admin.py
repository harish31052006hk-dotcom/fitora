from django.contrib import admin
from .models import Recipe, RecipeIngredient

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'servings', 'is_favorite_meal', 'updated_at')
    list_filter = ('is_favorite_meal',)
    search_fields = ('name', 'user__username')
    inlines = [RecipeIngredientInline]
