from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from django.utils import timezone

from .models import Recipe, RecipeIngredient
from .forms import RecipeForm, RecipeIngredientForm
from food_diary.models import FoodEntry

@login_required
def recipe_list_view(request):
    """
    Displays user recipes and saved favorite meals.
    """
    recipes = Recipe.objects.filter(user=request.user)
    filter_type = request.GET.get('tab', 'all')
    if filter_type == 'favorites':
        recipes = recipes.filter(is_favorite_meal=True)

    return render(request, 'recipes/recipe_list.html', {
        'recipes': recipes,
        'filter_type': filter_type,
        'title': 'My Meals & Recipes'
    })

@login_required
def recipe_detail_view(request, recipe_id):
    """
    Displays recipe details, nutritional breakdown, and one-click diary logging.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    ingredient_form = RecipeIngredientForm()

    if request.method == 'POST' and 'add_ingredient' in request.POST:
        ingredient_form = RecipeIngredientForm(request.POST)
        if ingredient_form.is_valid():
            ing = ingredient_form.save(commit=False)
            ing.recipe = recipe
            ing.save()
            messages.success(request, f"Added {ing.food_name} to {recipe.name}.")
            return redirect('recipe_detail', recipe_id=recipe.id)
        else:
            messages.error(request, "Please check the ingredient values.")

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredient_form': ingredient_form,
        'today_date': timezone.now().date().isoformat(),
        'title': recipe.name
    })

@login_required
def create_recipe_view(request):
    """
    Creates a new recipe or custom meal.
    """
    is_meal = request.GET.get('type') == 'meal'
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user
            if is_meal:
                recipe.is_favorite_meal = True
            recipe.save()
            messages.success(request, f"Recipe '{recipe.name}' created! Now add your ingredients below.")
            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        initial = {'is_favorite_meal': True} if is_meal else {}
        form = RecipeForm(initial=initial)

    return render(request, 'recipes/recipe_form.html', {
        'form': form,
        'is_meal': is_meal,
        'title': 'Create Saved Meal' if is_meal else 'Create Recipe'
    })

@login_required
def edit_recipe_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, f"Recipe '{recipe.name}' updated successfully.")
            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'recipes/recipe_form.html', {
        'form': form,
        'recipe': recipe,
        'is_edit': True,
        'title': f"Edit {recipe.name}"
    })

@login_required
def delete_recipe_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    name = recipe.name
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, f"Deleted '{name}'.")
        return redirect('recipe_list')
    return render(request, 'recipes/confirm_delete.html', {'recipe': recipe, 'title': f"Delete {name}"})

@login_required
def delete_ingredient_view(request, recipe_id, ingredient_id):
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    ingredient = get_object_or_404(RecipeIngredient, id=ingredient_id, recipe=recipe)
    ing_name = ingredient.food_name
    if request.method == 'POST':
        ingredient.delete()
        messages.success(request, f"Removed '{ing_name}' from recipe.")
    return redirect('recipe_detail', recipe_id=recipe.id)

@login_required
def log_recipe_to_diary(request, recipe_id):
    """
    Logs 1 serving (or custom servings) of a recipe into the user's daily food diary.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    
    if request.method == 'POST':
        meal_category = request.POST.get('meal_category', 'Lunch')
        date_str = request.POST.get('date', timezone.now().date().isoformat())
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            entry_date = timezone.now().date()

        servings_logged = Decimal(request.POST.get('servings', '1.0'))
        if servings_logged <= 0:
            servings_logged = Decimal('1.0')

        # Calculate nutrition for logged portion
        cals = (recipe.per_serving_calories * servings_logged).quantize(Decimal('0.01'))
        protein = (recipe.per_serving_protein * servings_logged).quantize(Decimal('0.01'))
        carbs = (recipe.per_serving_carbohydrates * servings_logged).quantize(Decimal('0.01'))
        fat = (recipe.per_serving_fat * servings_logged).quantize(Decimal('0.01'))

        FoodEntry.objects.create(
            user=request.user,
            date=entry_date,
            meal_category=meal_category,
            food_name=f"{recipe.name} ({servings_logged} serving{'s' if servings_logged != 1 else ''})",
            brand="My Recipes",
            serving_amount=servings_logged,
            serving_unit='serving',
            calories=cals,
            protein=protein,
            carbohydrates=carbs,
            fat=fat
        )

        messages.success(request, f"Logged {servings_logged} serving of '{recipe.name}' ({cals} kcal) to {meal_category}!")
        return redirect(f"/diary/?date={entry_date.isoformat()}")

    return redirect('recipe_detail', recipe_id=recipe.id)
