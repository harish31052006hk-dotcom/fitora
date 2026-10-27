from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import Profile
from food_diary.models import FoodEntry
from .models import WeeklyPlan
from .services import generate_weekly_plan


def _recent_diary_summary(user, start, end):
    entries = list(FoodEntry.objects.filter(user=user, date__range=(start, end)).order_by('date', 'created_at'))
    if not entries:
        return 'No food diary entries were recorded during the last seven days.'
    by_day = {}
    for entry in entries:
        day = entry.date.isoformat()
        bucket = by_day.setdefault(day, {'calories': Decimal('0'), 'protein': Decimal('0'), 'foods': []})
        bucket['calories'] += entry.calories
        bucket['protein'] += entry.protein
        if len(bucket['foods']) < 4:
            bucket['foods'].append(entry.food_name)
    lines = []
    for day, data in by_day.items():
        lines.append(f"{day}: {round(data['calories'])} kcal, {round(data['protein'])} g protein; logged foods: {', '.join(data['foods'])}.")
    average = sum((row['calories'] for row in by_day.values()), Decimal('0')) / max(1, len(by_day))
    return f"Logged on {len(by_day)} of the 7 days; average on logged days: {round(average)} kcal. " + ' '.join(lines)


@login_required
def weekly_plan_view(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    profile, _ = Profile.objects.get_or_create(user=request.user)
    existing_plan = WeeklyPlan.objects.filter(user=request.user, week_start=week_start).first()

    defaults = {
        'goal': 'general_health',
        'diet': 'flexible',
        'training_days': '3',
        'budget': 'moderate',
        'prep_time': '30',
        'foods_to_avoid': '',
    }
    if existing_plan:
        saved = existing_plan.preferences or {}
        defaults.update({key: str(saved.get(key, value)) for key, value in defaults.items()})

    if request.method == 'POST':
        allowed = {
            'goal': {'fat_loss', 'maintenance', 'muscle_gain', 'general_health'},
            'diet': {'flexible', 'vegetarian', 'vegan', 'high_protein', 'pescatarian'},
            'budget': {'low', 'moderate', 'flexible'},
            'prep_time': {'15', '30', '60'},
        }
        preferences = {}
        for key, options in allowed.items():
            value = request.POST.get(key, defaults.get(key, '')).strip()
            preferences[key] = value if value in options else defaults[key]
        try:
            training_days = int(request.POST.get('training_days', '3'))
        except (TypeError, ValueError):
            training_days = 3
        preferences['training_days'] = str(max(0, min(6, training_days)))
        preferences['foods_to_avoid'] = request.POST.get('foods_to_avoid', '').strip()[:300]
        diary_summary = _recent_diary_summary(request.user, today - timedelta(days=6), today)
        plan_data, source, note = generate_weekly_plan(profile, preferences, diary_summary)
        saved_plan, _created = WeeklyPlan.objects.update_or_create(
            user=request.user,
            week_start=week_start,
            defaults={
                'preferences': preferences,
                'plan_data': plan_data,
                'generation_source': source,
                'generation_note': note,
            },
        )
        if source == WeeklyPlan.SOURCE_AI:
            messages.success(request, 'Your weekly plan is ready. It is saved for this week and can be regenerated whenever your preferences change.')
        else:
            messages.warning(request, note or 'A starter plan was created. The AI provider was unavailable.')
        return redirect('weekly_plan')

    context = {
        'title': 'My Weekly Plan',
        'week_start': week_start,
        'week_end': week_end,
        'profile': profile,
        'plan': existing_plan,
        'plan_data': existing_plan.plan_data if existing_plan else {},
        'form_values': defaults,
        'training_day_options': [(str(value), f'{value} day' if value == 1 else f'{value} days') for value in range(7)],
    }
    return render(request, 'plans/weekly_plan.html', context)
