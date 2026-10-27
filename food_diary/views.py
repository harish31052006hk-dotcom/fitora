from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from .models import FoodEntry
from .forms import FoodEntryForm
from nutrition.models import FoodItem
from accounts.models import Profile

@login_required
def diary_view(request):
    """
    Daily Food Diary view with meal categories, date navigation, and daily totals.
    Calculates calories remaining = goal - consumed (allows negative values when goal exceeded).
    """
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    entries = FoodEntry.objects.filter(user=request.user, date=current_date)

    categories = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
    meals_data = {}
    total_calories = Decimal('0.00')
    total_protein = Decimal('0.00')
    total_carbs = Decimal('0.00')
    total_fat = Decimal('0.00')

    for cat in categories:
        cat_entries = entries.filter(meal_category=cat)
        cat_cals = sum((e.calories for e in cat_entries), Decimal('0.00'))
        cat_protein = sum((e.protein for e in cat_entries), Decimal('0.00'))
        cat_carbs = sum((e.carbohydrates for e in cat_entries), Decimal('0.00'))
        cat_fat = sum((e.fat for e in cat_entries), Decimal('0.00'))

        meals_data[cat] = {
            'entries': cat_entries,
            'count': cat_entries.count(),
            'calories': cat_cals,
            'protein': cat_protein,
            'carbohydrates': cat_carbs,
            'fat': cat_fat,
        }

        total_calories += cat_cals
        total_protein += cat_protein
        total_carbs += cat_carbs
        total_fat += cat_fat

    calorie_goal = Decimal(str(profile.daily_calorie_goal))
    calories_remaining = calorie_goal - total_calories
    goal_exceeded = calories_remaining < Decimal('0.00')
    exceeded_by = abs(calories_remaining) if goal_exceeded else Decimal('0.00')

    # Percentage calculations for progress bars
    cal_percent = min(100, int((total_calories / calorie_goal * 100))) if calorie_goal > 0 else 0
    protein_percent = min(100, int((total_protein / Decimal(str(profile.daily_protein_goal)) * 100))) if profile.daily_protein_goal > 0 else 0
    carbs_percent = min(100, int((total_carbs / Decimal(str(profile.daily_carbs_goal)) * 100))) if profile.daily_carbs_goal > 0 else 0
    fat_percent = min(100, int((total_fat / Decimal(str(profile.daily_fat_goal)) * 100))) if profile.daily_fat_goal > 0 else 0

    has_entries = entries.exists()

    context = {
        'current_date': current_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'is_today': current_date == timezone.now().date(),
        'profile': profile,
        'meals_data': meals_data,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fat': total_fat,
        'calorie_goal': calorie_goal,
        'calories_remaining': calories_remaining,
        'goal_exceeded': goal_exceeded,
        'exceeded_by': exceeded_by,
        'cal_percent': cal_percent,
        'protein_percent': protein_percent,
        'carbs_percent': carbs_percent,
        'fat_percent': fat_percent,
        'has_entries': has_entries,
        'title': f"Food Diary - {current_date.strftime('%B %d, %Y')}"
    }
    return render(request, 'food_diary/diary.html', context)

@login_required
def add_entry_view(request):
    """
    Adds a new food entry to the user's diary with server-side validation.
    """
    initial_meal = request.GET.get('meal', 'Breakfast')
    initial_date = request.GET.get('date', timezone.now().date().isoformat())
    food_id = request.GET.get('food_id')

    initial_data = {
        'meal_category': initial_meal,
        'date': initial_date,
        'quantity': Decimal('1.00'),
        'serving_amount': Decimal('100.00'),
        'serving_unit': 'g',
    }

    if food_id:
        try:
            food = FoodItem.objects.get(id=food_id)
            initial_data.update({
                'food_name': food.name,
                'brand': food.brand,
                'serving_amount': food.serving_size,
                'serving_unit': food.serving_unit,
                'calories': food.calories,
                'protein': food.protein,
                'carbohydrates': food.carbohydrates,
                'fat': food.fat,
                'base_serving_size': food.serving_size,
                'base_calories': food.calories,
                'base_protein': food.protein,
                'base_carbohydrates': food.carbohydrates,
                'base_fat': food.fat,
            })
        except FoodItem.DoesNotExist:
            pass

    if request.method == 'POST':
        form = FoodEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            # Link food item if provided
            post_food_id = request.POST.get('food_id')
            if post_food_id:
                try:
                    entry.food_item = FoodItem.objects.get(id=post_food_id)
                except FoodItem.DoesNotExist:
                    pass
            entry.save()
            messages.success(request, f"Added {entry.food_name} ({entry.calories} kcal) to {entry.meal_category}.")
            return redirect(f"/diary/?date={entry.date.isoformat()}")
        else:
            messages.error(request, "Please correct the entry values below.")
    else:
        form = FoodEntryForm(initial=initial_data)

    return render(request, 'food_diary/entry_form.html', {
        'form': form,
        'is_edit': False,
        'selected_meal': initial_meal,
        'selected_date': initial_date,
        'title': 'Add Food Entry'
    })

@login_required
def edit_entry_view(request, entry_id):
    """
    Edits an existing entry. Protected so users can ONLY edit their own entries.
    """
    entry = get_object_or_404(FoodEntry, id=entry_id, user=request.user)

    if request.method == 'POST':
        form = FoodEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {entry.food_name} ({entry.calories} kcal).")
            return redirect(f"/diary/?date={entry.date.isoformat()}")
        else:
            messages.error(request, "Please correct the entry values below.")
    else:
        form = FoodEntryForm(instance=entry)

    return render(request, 'food_diary/entry_form.html', {
        'form': form,
        'entry': entry,
        'is_edit': True,
        'title': f"Edit Entry: {entry.food_name}"
    })

@login_required
def delete_entry_view(request, entry_id):
    """
    Deletes an existing entry. Protected so users can ONLY delete their own entries.
    """
    entry = get_object_or_404(FoodEntry, id=entry_id, user=request.user)
    date_str = entry.date.isoformat()
    food_name = entry.food_name

    if request.method == 'POST':
        entry.delete()
        messages.success(request, f"Removed {food_name} from your food diary.")
        return redirect(f"/diary/?date={date_str}")

    return render(request, 'food_diary/confirm_delete.html', {
        'entry': entry,
        'title': f"Delete {entry.food_name}"
    })
