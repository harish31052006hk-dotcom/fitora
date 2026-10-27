from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Recipe, RecipeIngredient, SavedMeal, SavedMealItem
from .forms import RecipeForm, RecipeIngredientForm, SavedMealForm, SavedMealItemForm
from food_diary.models import FoodEntry
from nutrition.models import FoodItem

# ==============================================================================
# RECIPE VIEWS
# ==============================================================================

@login_required
def recipe_list_view(request):
    """
    Displays user recipes and favorite meals.
    """
    recipes = Recipe.objects.filter(user=request.user)
    saved_meals = SavedMeal.objects.filter(user=request.user)

    filter_type = request.GET.get('tab', 'all')
    if filter_type == 'favorites':
        recipes = recipes.filter(is_favorite_meal=True)

    return render(request, 'recipes/recipe_list.html', {
        'recipes': recipes,
        'saved_meals': saved_meals,
        'filter_type': filter_type,
        'title': 'My Meals & Recipes'
    })

@login_required
def recipe_detail_view(request, recipe_id):
    """
    Displays recipe details, ingredients list, and per-serving nutrition.
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
    Creates a new custom recipe.
    """
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = request.user
            recipe.save()
            messages.success(request, f"Recipe '{recipe.name}' created! Add ingredients below.")
            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm()

    return render(request, 'recipes/recipe_form.html', {
        'form': form,
        'title': 'Create Recipe'
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
    Logs 1 or more servings of a recipe into the user's food diary.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    
    if request.method == 'POST':
        meal_category = request.POST.get('meal_category', 'Lunch')
        date_str = request.POST.get('date', timezone.now().date().isoformat())
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            entry_date = timezone.now().date()

        try:
            servings_logged = Decimal(request.POST.get('servings', '1.0'))
        except (ValueError, TypeError):
            servings_logged = Decimal('1.0')

        if servings_logged <= 0:
            servings_logged = Decimal('1.0')

        cals = (recipe.per_serving_calories * servings_logged).quantize(Decimal('0.01'))
        protein = (recipe.per_serving_protein * servings_logged).quantize(Decimal('0.01'))
        carbs = (recipe.per_serving_carbohydrates * servings_logged).quantize(Decimal('0.01'))
        fat = (recipe.per_serving_fat * servings_logged).quantize(Decimal('0.01'))

        FoodEntry.objects.create(
            user=request.user,
            date=entry_date,
            meal_category=meal_category,
            food_name=f"{recipe.name} ({servings_logged} portion{'s' if servings_logged != 1 else ''})",
            brand="Recipe",
            quantity=servings_logged,
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

# ==============================================================================
# SAVED MEALS VIEWS
# ==============================================================================

@login_required
def saved_meals_list_view(request):
    """
    Lists user's saved meals representing actual food items and quantities.
    """
    saved_meals = SavedMeal.objects.filter(user=request.user)
    return render(request, 'recipes/saved_meals_list.html', {
        'saved_meals': saved_meals,
        'title': 'My Saved Meals'
    })

@login_required
def create_saved_meal_view(request):
    """
    Creates a new named saved meal.
    """
    if request.method == 'POST':
        form = SavedMealForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = request.user
            meal.save()
            messages.success(request, f"Saved Meal '{meal.name}' created! Now add the food items that make up this meal.")
            return redirect('saved_meal_detail', meal_id=meal.id)
    else:
        form = SavedMealForm()

    return render(request, 'recipes/saved_meal_form.html', {
        'form': form,
        'title': 'Create Saved Meal'
    })

@login_required
def saved_meal_detail_view(request, meal_id):
    """
    Displays saved meal items, calculated totals, and option to add items or log to diary.
    """
    meal = get_object_or_404(SavedMeal, id=meal_id, user=request.user)
    available_foods = FoodItem.objects.all().order_by('name')
    items = meal.items.all().select_related('food_item')

    if request.method == 'POST':
        food_item_id = request.POST.get('food_item')
        food_name = request.POST.get('food_name')
        quantity_str = request.POST.get('quantity', '1.0')
        serving_unit = request.POST.get('serving_unit', 'serving')

        try:
            quantity = Decimal(quantity_str)
        except (ValueError, TypeError):
            quantity = Decimal('1.00')

        if quantity <= Decimal('0.00'):
            messages.error(request, "Item quantity must be greater than zero.")
            return redirect('saved_meal_detail', meal_id=meal.id)

        food_item = None
        if food_item_id:
            try:
                food_item = FoodItem.objects.get(id=food_item_id)
                food_name = food_item.name
                serving_unit = food_item.serving_unit or 'serving'
                calories = (food_item.calories_per_serving * quantity).quantize(Decimal('0.01'))
                protein = (food_item.protein_per_serving * quantity).quantize(Decimal('0.01'))
                carbohydrates = (food_item.carbs_per_serving * quantity).quantize(Decimal('0.01'))
                fat = (food_item.fat_per_serving * quantity).quantize(Decimal('0.01'))
            except FoodItem.DoesNotExist:
                messages.error(request, "Selected food item does not exist.")
                return redirect('saved_meal_detail', meal_id=meal.id)
        elif food_name:
            # Custom manual entry
            try:
                calories = Decimal(request.POST.get('calories', '0.00')) * quantity
                protein = Decimal(request.POST.get('protein', '0.00')) * quantity
                carbohydrates = Decimal(request.POST.get('carbohydrates', '0.00')) * quantity
                fat = Decimal(request.POST.get('fat', '0.00')) * quantity
            except (ValueError, TypeError):
                calories = protein = carbohydrates = fat = Decimal('0.00')
        else:
            messages.error(request, "Please select or enter a food item.")
            return redirect('saved_meal_detail', meal_id=meal.id)

        SavedMealItem.objects.create(
            saved_meal=meal,
            food_item=food_item,
            food_name=food_name,
            quantity=quantity,
            serving_unit=serving_unit,
            calories=calories,
            protein=protein,
            carbohydrates=carbohydrates,
            fat=fat
        )
        messages.success(request, f"Added {food_name} ({calories} kcal) to '{meal.name}'.")
        return redirect('saved_meal_detail', meal_id=meal.id)

    item_form = SavedMealItemForm()

    return render(request, 'recipes/saved_meal_detail.html', {
        'meal': meal,
        'items': items,
        'available_foods': available_foods,
        'item_form': item_form,
        'today': timezone.now().date().isoformat(),
        'today_date': timezone.now().date().isoformat(),
        'title': meal.name
    })

@login_required
def edit_saved_meal_view(request, meal_id):
    meal = get_object_or_404(SavedMeal, id=meal_id, user=request.user)
    if request.method == 'POST':
        form = SavedMealForm(request.POST, instance=meal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Saved meal '{meal.name}' updated.")
            return redirect('saved_meal_detail', meal_id=meal.id)
    else:
        form = SavedMealForm(instance=meal)

    return render(request, 'recipes/saved_meal_form.html', {
        'form': form,
        'meal': meal,
        'is_edit': True,
        'title': f"Edit {meal.name}"
    })

@login_required
def delete_saved_meal_view(request, meal_id):
    meal = get_object_or_404(SavedMeal, id=meal_id, user=request.user)
    name = meal.name
    if request.method == 'POST':
        meal.delete()
        messages.success(request, f"Deleted saved meal '{name}'.")
        return redirect('saved_meals_list')
    return render(request, 'recipes/saved_meal_confirm_delete.html', {
        'meal': meal,
        'title': f"Delete {name}"
    })

@login_required
def delete_saved_meal_item_view(request, meal_id, item_id):
    meal = get_object_or_404(SavedMeal, id=meal_id, user=request.user)
    item = get_object_or_404(SavedMealItem, id=item_id, saved_meal=meal)
    item_name = item.food_name
    if request.method == 'POST':
        item.delete()
        messages.success(request, f"Removed '{item_name}' from {meal.name}.")
    return redirect('saved_meal_detail', meal_id=meal.id)

@login_required
def log_saved_meal_to_diary_view(request, meal_id):
    """
    Logs all underlying food items in a Saved Meal into the user's food diary
    for the chosen meal category and date.
    """
    meal = get_object_or_404(SavedMeal, id=meal_id, user=request.user)
    
    if request.method == 'POST':
        meal_category = request.POST.get('meal_category', 'Breakfast')
        date_str = request.POST.get('date', timezone.now().date().isoformat())
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            entry_date = timezone.now().date()

        items = meal.items.all()
        if not items.exists():
            messages.warning(request, f"'{meal.name}' contains no food items yet. Please add food items to the meal before logging.")
            return redirect('saved_meal_detail', meal_id=meal.id)

        # Create food diary entries for every item in the saved meal
        logged_count = 0
        total_logged_cals = Decimal('0.00')

        for item in items:
            FoodEntry.objects.create(
                user=request.user,
                food_item=item.food_item,
                date=entry_date,
                meal_category=meal_category,
                food_name=item.food_name,
                brand=f"Saved Meal: {meal.name}",
                quantity=item.quantity,
                serving_amount=item.quantity,
                serving_unit=item.serving_unit,
                calories=item.calories,
                protein=item.protein,
                carbohydrates=item.carbohydrates,
                fat=item.fat
            )
            logged_count += 1
            total_logged_cals += item.calories

        messages.success(
            request,
            f"Successfully logged saved meal '{meal.name}' ({logged_count} items, {total_logged_cals} kcal) to {meal_category}!"
        )
        return redirect(f"/diary/?date={entry_date.isoformat()}")

    return redirect('saved_meal_detail', meal_id=meal.id)
