import json
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from .models import WeightLog
from .forms import WeightLogForm
from accounts.models import Profile
from food_diary.models import FoodEntry

@login_required
def progress_view(request):
    """
    Renders the progress analytics dashboard with interactive Chart.js charts.
    Includes weight tracking, calorie trend vs goal, and macronutrient distribution.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    today = timezone.now().date()

    # Form handling for recording weight
    if request.method == 'POST':
        form = WeightLogForm(request.POST)
        if form.is_valid():
            weight_log, created = WeightLog.objects.update_or_create(
                user=request.user,
                date=form.cleaned_data['date'],
                defaults={
                    'weight': form.cleaned_data['weight'],
                    'notes': form.cleaned_data.get('notes', '')
                }
            )
            # Update user profile's current weight
            profile.current_weight = weight_log.weight
            profile.save()
            action = "Recorded" if created else "Updated"
            messages.success(request, f"{action} weight entry for {weight_log.date} ({weight_log.weight} kg).")
            return redirect('progress')
        else:
            messages.error(request, "Please correct the weight entry values.")
    else:
        form = WeightLogForm(initial={'date': today.isoformat(), 'weight': profile.current_weight})

    # Historical Weight Data
    weight_logs = WeightLog.objects.filter(user=request.user).order_by('date')
    weight_labels = [log.date.strftime('%b %d') for log in weight_logs]
    weight_values = [float(log.weight) for log in weight_logs]
    target_weight_value = float(profile.target_weight) if profile.target_weight else None

    # Last 7 Days Calorie History
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    cal_labels = [d.strftime('%a (%b %d)') for d in last_7_days]
    cal_values = []
    daily_goal_values = [profile.daily_calorie_goal] * 7

    total_week_cals = Decimal('0.00')
    total_week_protein = Decimal('0.00')
    total_week_carbs = Decimal('0.00')
    total_week_fat = Decimal('0.00')

    for day in last_7_days:
        day_entries = FoodEntry.objects.filter(user=request.user, date=day)
        day_cal = sum((e.calories for e in day_entries), Decimal('0.00'))
        cal_values.append(float(day_cal))
        total_week_cals += day_cal
        total_week_protein += sum((e.protein for e in day_entries), Decimal('0.00'))
        total_week_carbs += sum((e.carbohydrates for e in day_entries), Decimal('0.00'))
        total_week_fat += sum((e.fat for e in day_entries), Decimal('0.00'))

    # Average daily calories over past week
    active_days = sum(1 for c in cal_values if c > 0)
    avg_calories = round(float(total_week_cals) / max(1, active_days), 1) if active_days > 0 else 0

    # Macro distribution for doughnut chart
    macro_data = {
        'protein': float(total_week_protein),
        'carbs': float(total_week_carbs),
        'fat': float(total_week_fat)
    }

    context = {
        'profile': profile,
        'form': form,
        'weight_logs': weight_logs.reverse()[:10], # Show recent 10 in table
        'avg_calories': avg_calories,
        'active_days': active_days,
        'chart_weight_labels_json': json.dumps(weight_labels),
        'chart_weight_values_json': json.dumps(weight_values),
        'target_weight_value': target_weight_value,
        'chart_cal_labels_json': json.dumps(cal_labels),
        'chart_cal_values_json': json.dumps(cal_values),
        'chart_goal_values_json': json.dumps(daily_goal_values),
        'chart_macro_json': json.dumps(macro_data),
        'title': 'Progress & Analytics'
    }
    return render(request, 'progress/progress.html', context)

@login_required
def delete_weight_view(request, log_id):
    log = get_object_or_404(WeightLog, id=log_id, user=request.user)
    if request.method == 'POST':
        date_str = log.date.strftime('%b %d, %Y')
        log.delete()
        messages.success(request, f"Deleted weight entry for {date_str}.")
    return redirect('progress')
