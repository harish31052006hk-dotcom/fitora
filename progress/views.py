import json
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import WeightLog
from .forms import WeightLogForm
from accounts.models import Profile
from food_diary.models import FoodEntry

@login_required
def progress_view(request):
    """
    Renders the progress analytics dashboard with interactive Chart.js charts:
    - Daily calorie intake vs calorie goal
    - Weekly calorie trends
    - Macronutrient distribution (Protein, Carbs, Fat)
    - Weight history over time
    - Summary metrics: Average daily calories, days tracked, latest weight, weight change
    - Date filtering: 7 days, 30 days, or custom date range
    - Pure actual user data with useful empty states (never invented).
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    today = timezone.now().date()

    # Weight logging form submission
    if request.method == 'POST':
        form = WeightLogForm(request.POST)
        if form.is_valid():
            log_date = form.cleaned_data['date']
            weight_val = form.cleaned_data['weight']
            notes_val = form.cleaned_data.get('notes', '')

            weight_log, created = WeightLog.objects.update_or_create(
                user=request.user,
                date=log_date,
                defaults={
                    'weight': weight_val,
                    'notes': notes_val
                }
            )

            # Update profile current weight if this is the newest weigh-in
            latest_log = WeightLog.objects.filter(user=request.user).order_by('-date').first()
            if latest_log and latest_log.date <= today:
                profile.current_weight = latest_log.weight
                profile.save()

            action = "Recorded" if created else "Updated"
            messages.success(request, f"{action} weight entry for {weight_log.date.strftime('%b %d, %Y')} ({weight_log.weight} kg).")
            return redirect('progress')
        else:
            messages.error(request, "Please correct the weight entry values.")
    else:
        form = WeightLogForm(initial={'date': today.isoformat(), 'weight': profile.current_weight})

    # Date range filter handling: '7' (default), '30', or 'custom'
    range_filter = request.GET.get('range', '7')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if range_filter == '30':
        start_date = today - timedelta(days=29)
        end_date = today
    elif range_filter == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date > end_date:
                start_date, end_date = end_date, start_date
        except ValueError:
            range_filter = '7'
            start_date = today - timedelta(days=6)
            end_date = today
    else:
        range_filter = '7'
        start_date = today - timedelta(days=6)
        end_date = today

    # Generate daily date series between start_date and end_date
    num_days = (end_date - start_date).days + 1
    # Cap maximum query days to 90 for performance and readable chart scale
    if num_days > 90:
        num_days = 90
        start_date = end_date - timedelta(days=89)

    date_series = [start_date + timedelta(days=i) for i in range(num_days)]

    # 1. Fetch user Food Entries for selected date range
    range_entries = FoodEntry.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    )

    daily_calories_map = {}
    daily_protein_map = {}
    daily_carbs_map = {}
    daily_fat_map = {}

    for entry in range_entries:
        d = entry.date
        daily_calories_map[d] = daily_calories_map.get(d, Decimal('0.00')) + entry.calories
        daily_protein_map[d] = daily_protein_map.get(d, Decimal('0.00')) + entry.protein
        daily_carbs_map[d] = daily_carbs_map.get(d, Decimal('0.00')) + entry.carbohydrates
        daily_fat_map[d] = daily_fat_map.get(d, Decimal('0.00')) + entry.fat

    chart_daily_cal_labels = [d.strftime('%b %d') for d in date_series]
    chart_daily_cal_values = [float(daily_calories_map.get(d, Decimal('0.00'))) for d in date_series]
    chart_daily_goal_values = [int(profile.daily_calorie_goal)] * num_days

    # Aggregations for selected range
    total_range_calories = sum(daily_calories_map.values(), Decimal('0.00'))
    total_range_protein = sum(daily_protein_map.values(), Decimal('0.00'))
    total_range_carbs = sum(daily_carbs_map.values(), Decimal('0.00'))
    total_range_fat = sum(daily_fat_map.values(), Decimal('0.00'))

    # Days tracked: count of dates with at least one food entry
    days_tracked = len(daily_calories_map)
    avg_daily_calories = round(float(total_range_calories) / max(1, days_tracked), 1) if days_tracked > 0 else 0

    # Macro distribution
    has_macro_data = (total_range_protein + total_range_carbs + total_range_fat) > Decimal('0.00')
    macro_data = {
        'protein': float(total_range_protein),
        'carbs': float(total_range_carbs),
        'fat': float(total_range_fat)
    }

    # 2. Weekly Calorie Trends (Aggregated by calendar week for up to last 4 weeks)
    weekly_trend_labels = []
    weekly_trend_consumed = []
    weekly_trend_goal = []

    for w in range(3, -1, -1):
        w_end = today - timedelta(days=w * 7)
        w_start = w_end - timedelta(days=6)
        w_entries = FoodEntry.objects.filter(user=request.user, date__gte=w_start, date__lte=w_end)
        w_cals = sum((e.calories for e in w_entries), Decimal('0.00'))
        
        label_str = f"{w_start.strftime('%b %d')} - {w_end.strftime('%b %d')}"
        weekly_trend_labels.append(label_str)
        weekly_trend_consumed.append(float(w_cals))
        weekly_trend_goal.append(int(profile.daily_calorie_goal * 7))

    has_weekly_trend_data = any(c > 0 for c in weekly_trend_consumed)

    # 3. User Weight Logs & Analytics
    all_weight_logs = WeightLog.objects.filter(user=request.user).order_by('date')
    range_weight_logs = all_weight_logs.filter(date__gte=start_date, date__lte=end_date)

    # Use range logs if present, otherwise show historical logs so chart is meaningful
    display_weight_logs = range_weight_logs if range_weight_logs.exists() else all_weight_logs

    chart_weight_labels = [log.date.strftime('%b %d') for log in display_weight_logs]
    chart_weight_values = [float(log.weight) for log in display_weight_logs]
    target_weight_val = float(profile.target_weight) if profile.target_weight else None

    # Weight Summary Calculations
    latest_weight_log = all_weight_logs.last()
    first_weight_log = all_weight_logs.first()

    latest_weight = latest_weight_log.weight if latest_weight_log else profile.current_weight
    weight_change = None
    weight_change_direction = 'none'

    if all_weight_logs.count() >= 2:
        diff = latest_weight_log.weight - first_weight_log.weight
        weight_change = abs(diff)
        if diff > 0:
            weight_change_direction = 'gain'
        elif diff < 0:
            weight_change_direction = 'loss'
        else:
            weight_change_direction = 'steady'

    context = {
        'profile': profile,
        'form': form,
        'today': today,
        'range_filter': range_filter,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'start_date_display': start_date.strftime('%b %d, %Y'),
        'end_date_display': end_date.strftime('%b %d, %Y'),
        'num_days': num_days,

        # Summary KPIs
        'days_tracked': days_tracked,
        'avg_daily_calories': avg_daily_calories,
        'total_range_calories': total_range_calories,
        'latest_weight': latest_weight,
        'weight_change': weight_change,
        'weight_change_direction': weight_change_direction,
        'first_weight_date': first_weight_log.date if first_weight_log else None,
        'total_weigh_ins': all_weight_logs.count(),

        # Weight History Records (most recent first for table)
        'weight_records': all_weight_logs.reverse()[:15],
        'has_weight_records': all_weight_logs.exists(),

        # Chart.js JSON serializations
        'has_calorie_data': any(c > 0 for c in chart_daily_cal_values),
        'chart_daily_cal_labels_json': json.dumps(chart_daily_cal_labels),
        'chart_daily_cal_values_json': json.dumps(chart_daily_cal_values),
        'chart_daily_goal_values_json': json.dumps(chart_daily_goal_values),

        'has_macro_data': has_macro_data,
        'chart_macro_json': json.dumps(macro_data),

        'has_weekly_trend_data': has_weekly_trend_data,
        'chart_weekly_labels_json': json.dumps(weekly_trend_labels),
        'chart_weekly_consumed_json': json.dumps(weekly_trend_consumed),
        'chart_weekly_goal_json': json.dumps(weekly_trend_goal),

        'has_weight_data': len(chart_weight_values) > 0,
        'chart_weight_labels_json': json.dumps(chart_weight_labels),
        'chart_weight_values_json': json.dumps(chart_weight_values),
        'target_weight_val': target_weight_val,

        'title': 'Progress & Analytics'
    }
    return render(request, 'progress/progress.html', context)

@login_required
def edit_weight_view(request, log_id):
    """
    Allows user to edit their own previous weight measurement record.
    Enforces user data isolation.
    """
    log = get_object_or_404(WeightLog, id=log_id, user=request.user)

    if request.method == 'POST':
        form = WeightLogForm(request.POST, instance=log)
        if form.is_valid():
            updated_log = form.save()
            # Update user profile current weight if this is the newest weigh-in
            latest_log = WeightLog.objects.filter(user=request.user).order_by('-date').first()
            if latest_log:
                profile = request.user.profile
                profile.current_weight = latest_log.weight
                profile.save()

            messages.success(request, f"Updated weight record for {updated_log.date.strftime('%b %d, %Y')} ({updated_log.weight} kg).")
            return redirect('progress')
        else:
            messages.error(request, "Please correct the weight entry values.")
    else:
        form = WeightLogForm(instance=log)

    return render(request, 'progress/weight_edit_form.html', {
        'form': form,
        'log': log,
        'title': f"Edit Weight Record — {log.date.strftime('%b %d, %Y')}"
    })

@login_required
def delete_weight_view(request, log_id):
    """
    Allows user to delete their own previous weight measurement record.
    Enforces user data isolation.
    """
    log = get_object_or_404(WeightLog, id=log_id, user=request.user)
    if request.method == 'POST':
        date_str = log.date.strftime('%b %d, %Y')
        log.delete()

        # Update profile's current weight to the remaining latest record if any
        remaining_latest = WeightLog.objects.filter(user=request.user).order_by('-date').first()
        profile = request.user.profile
        profile.current_weight = remaining_latest.weight if remaining_latest else None
        profile.save()

        messages.success(request, f"Deleted weight entry for {date_str}.")
    return redirect('progress')
