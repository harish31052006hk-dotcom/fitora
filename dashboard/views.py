import json
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from accounts.models import Profile
from food_diary.models import FoodEntry
from recipes.models import Recipe
from support.models import FAQ

def home_view(request):
    """
    Public landing page for visitors with hero banner, feature highlights, and FAQ previews.
    If user is authenticated, redirects to personal dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    preview_faqs = FAQ.objects.filter(is_active=True)[:4]

    return render(request, 'dashboard/home.html', {
        'preview_faqs': preview_faqs,
        'title': 'Fitora — Your Goals. Your Journey. Your Fit.'
    })

@login_required
def dashboard_view(request):
    """
    Personalized fitness and nutrition dashboard calculated from actual database records.
    Displays daily calories, remaining energy balance, macro rings, recent entries, and charts.
    """
    # Allow viewing a specific date via GET parameter or default to today
    date_str = request.GET.get('date')
    if date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    today = selected_date
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Fetch selected day's food entries
    today_entries = FoodEntry.objects.filter(user=request.user, date=today)

    # Calculate actual consumed totals using Decimal
    calories_consumed = sum((e.calories for e in today_entries), Decimal('0.00'))
    protein_consumed = sum((e.protein for e in today_entries), Decimal('0.00'))
    carbs_consumed = sum((e.carbohydrates for e in today_entries), Decimal('0.00'))
    fat_consumed = sum((e.fat for e in today_entries), Decimal('0.00'))

    # Targets from user profile
    calorie_goal = Decimal(str(profile.daily_calorie_goal))
    protein_goal = Decimal(str(profile.daily_protein_goal))
    carbs_goal = Decimal(str(profile.daily_carbs_goal))
    fat_goal = Decimal(str(profile.daily_fat_goal))

    # Formula: Calories Remaining = Calorie Goal - Calories Consumed
    calories_remaining = calorie_goal - calories_consumed
    goal_exceeded = calories_remaining < Decimal('0.00')
    exceeded_by = abs(calories_remaining) if goal_exceeded else Decimal('0.00')

    # Calculate percentages for UI progress rings
    cal_percentage = min(100, int((calories_consumed / calorie_goal * 100))) if calorie_goal > 0 else 0
    protein_percentage = min(100, int((protein_consumed / protein_goal * 100))) if protein_goal > 0 else 0
    carbs_percentage = min(100, int((carbs_consumed / carbs_goal * 100))) if carbs_goal > 0 else 0
    fat_percentage = min(100, int((fat_consumed / fat_goal * 100))) if fat_goal > 0 else 0

    # Categorize today's meals
    categories = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
    today_meals = {}
    for cat in categories:
        cat_entries = today_entries.filter(meal_category=cat)
        today_meals[cat] = {
            'entries': cat_entries,
            'count': cat_entries.count(),
            'calories': sum((e.calories for e in cat_entries), Decimal('0.00'))
        }

    # Recent entries (last 5 entries)
    recent_entries = FoodEntry.objects.filter(user=request.user).order_by('-date', '-created_at')[:5]

    # Weekly calorie chart (last 7 days)
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%a') for d in last_7_days]
    chart_calories = []
    chart_goal_line = [int(profile.daily_calorie_goal)] * 7

    for d in last_7_days:
        day_entries = FoodEntry.objects.filter(user=request.user, date=d)
        day_cals = sum((e.calories for e in day_entries), Decimal('0.00'))
        chart_calories.append(float(day_cals))

    # Favorite meals for quick add
    favorite_recipes = Recipe.objects.filter(user=request.user, is_favorite_meal=True)[:4]

    context = {
        'profile': profile,
        'today': today,
        'calories_consumed': calories_consumed,
        'calorie_goal': calorie_goal,
        'calories_remaining': calories_remaining,
        'goal_exceeded': goal_exceeded,
        'exceeded_by': exceeded_by,
        'protein_consumed': protein_consumed,
        'protein_goal': protein_goal,
        'carbs_consumed': carbs_consumed,
        'carbs_goal': carbs_goal,
        'fat_consumed': fat_consumed,
        'fat_goal': fat_goal,
        'cal_percentage': cal_percentage,
        'protein_percentage': protein_percentage,
        'carbs_percentage': carbs_percentage,
        'fat_percentage': fat_percentage,
        'today_meals': today_meals,
        'recent_entries': recent_entries,
        'has_entries': today_entries.exists(),
        'favorite_recipes': favorite_recipes,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_calories_json': json.dumps(chart_calories),
        'chart_goal_json': json.dumps(chart_goal_line),
        'title': 'My Dashboard'
    }
    return render(request, 'dashboard/dashboard.html', context)
