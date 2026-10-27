"""AI-assisted weekly planning with a clearly labelled deterministic fallback."""
import json
import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger('fitora.plans')

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

BREAKFASTS = [
    ('Oats with yogurt and fruit', 'Oats, plain yogurt, seasonal fruit and seeds.'),
    ('Eggs or tofu with whole-grain toast', 'Add tomatoes or other vegetables.'),
    ('Idli with sambar', 'A practical, fibre-containing breakfast.'),
    ('Greek yogurt or curd bowl', 'Add fruit, oats and a small portion of nuts.'),
    ('Vegetable poha with curd', 'Include peas or another protein side when possible.'),
    ('Paneer or tofu bhurji wrap', 'Use a whole-wheat wrap and vegetables.'),
    ('Besan chilla with curd', 'Add vegetables to the batter.'),
]
LUNCHES = [
    ('Rice, dal and vegetables', 'Build the plate around dal, vegetables and a measured rice portion.'),
    ('Chicken or chickpea grain bowl', 'Pair a protein source with grains and crunchy vegetables.'),
    ('Chapati, paneer or tofu and sabzi', 'Include a protein-rich main and vegetables.'),
    ('Bean and vegetable rice bowl', 'Add curd or another protein side if desired.'),
    ('Fish or tofu with rice and greens', 'Use a familiar portion and avoid relying on sauces for flavour.'),
    ('Rajma with rice and salad', 'Include beans and a side of vegetables.'),
    ('Egg, tofu or paneer wrap', 'Add salad vegetables and a yogurt-based sauce.'),
]
DINNERS = [
    ('Dal, chapati and vegetables', 'A balanced home-style meal with a protein source.'),
    ('Stir-fried tofu or chicken with vegetables', 'Serve with rice or another grain.'),
    ('Vegetable khichdi with curd', 'Adjust the portion to your personal target.'),
    ('Paneer or bean bowl', 'Combine protein, vegetables and a moderate grain portion.'),
    ('Fish or chickpea curry with rice', 'Add vegetables and use oil mindfully.'),
    ('Lentil soup with toast', 'Add a protein side if this meal leaves you hungry.'),
    ('Egg or tofu fried rice', 'Use plenty of vegetables and a measured oil portion.'),
]
SNACKS = [
    ('Fruit and a small handful of nuts', 'A convenient snack; adjust nuts to your energy target.'),
    ('Curd or yogurt with fruit', 'Choose unsweetened when practical.'),
    ('Roasted chickpeas', 'A portable option with fibre and some protein.'),
    ('Boiled eggs or edamame', 'Use the option that fits your dietary preference.'),
    ('Milk or fortified soy drink', 'A simple option when you need something quick.'),
    ('Hummus with vegetables', 'Add whole-grain crackers if you need more energy.'),
    ('Paneer cubes or tofu bites', 'Season simply and keep chilled until needed.'),
]


def _fallback_plan(profile, preferences, diary_summary):
    target = int(getattr(profile, 'daily_calorie_goal', 2000) or 2000)
    protein_target = int(getattr(profile, 'daily_protein_goal', 120) or 120)
    carbs_target = int(getattr(profile, 'daily_carbs_goal', 220) or 220)
    fat_target = int(getattr(profile, 'daily_fat_goal', 65) or 65)
    goal = preferences.get('goal', 'general_health')
    diet = preferences.get('diet', 'flexible')

    def adapt(name, description):
        if diet in ('vegetarian', 'vegan') and 'eggs or tofu' in name.lower():
            name = 'Tofu scramble with whole-grain toast'
        if diet in ('vegetarian', 'vegan'):
            substitutions = [('chicken', 'chickpeas'), ('fish', 'tofu'), ('eggs', 'tofu'), ('egg', 'tofu')]
            if diet == 'vegan':
                substitutions += [('yogurt', 'soy yogurt'), ('curd', 'fortified soy yogurt'), ('paneer', 'tofu'), ('milk', 'fortified soy drink')]
            for old, new in substitutions:
                name = re.sub(old, new, name, flags=re.I)
                description = re.sub(old, new, description, flags=re.I)
        elif diet == 'pescatarian':
            name = re.sub('chicken', 'beans', name, flags=re.I)
            description = re.sub('chicken', 'beans', description, flags=re.I)
        return name, description

    if goal == 'fat_loss':
        focus = 'Build consistent, satisfying meals around your saved calorie target; avoid aggressive restriction.'
    elif goal == 'muscle_gain':
        focus = 'Support training with regular meals, protein-containing foods and enough total energy.'
    elif goal == 'maintenance':
        focus = 'Keep meals consistent and use your logged trend to make small adjustments over time.'
    else:
        focus = 'Prioritise regular meals, variety, vegetables, protein and a routine you can sustain.'

    try:
        training_count = max(0, min(6, int(preferences.get('training_days', 3))))
    except (TypeError, ValueError, OverflowError):
        training_count = 3
    if training_count == 0:
        training_indices = set()
    else:
        training_indices = {round(i * 6 / max(1, training_count - 1)) for i in range(training_count)}

    days = []
    for index, day in enumerate(DAY_NAMES):
        meal_sets = [BREAKFASTS[index], LUNCHES[index], DINNERS[index], SNACKS[index]]
        meal_ratios = [('Breakfast', .25), ('Lunch', .35), ('Dinner', .30), ('Snack', .10)]
        meals = []
        for (name, description), (kind, ratio) in zip(meal_sets, meal_ratios):
            name, description = adapt(name, description)
            meals.append({
                'type': kind,
                'name': name,
                'description': description,
                'calories_kcal': max(80, round(target * ratio)),
                'protein_g': max(3, round(protein_target * ratio)),
            })
        if index in training_indices:
            movement = 'Planned training day: use your familiar routine and scale intensity to your recovery.'
        else:
            movement = 'Recovery day: walking, mobility or rest according to energy and schedule.'
        habit_options = [
            'Log your main meals before the day ends.',
            'Include a protein source in two or more meals.',
            'Add a vegetable or fruit serving to a meal.',
            'Prepare one meal or snack ahead of time.',
            'Review hunger and energy rather than chasing perfect numbers.',
            'Keep a water bottle nearby and drink regularly.',
            'Review the week without judging one individual day.',
        ]
        days.append({
            'day': day,
            'focus': ['Start simple', 'Keep it balanced', 'Make prep easier', 'Stay flexible', 'Use familiar meals', 'Enjoy variety', 'Review and reset'][index],
            'meals': meals,
            'movement': movement,
            'habit': habit_options[index],
        })

    return {
        'title': 'Your weekly rhythm',
        'summary': 'A flexible starter plan built around your current Fitora targets. Treat meal calories as rough estimates, not exact measurements.',
        'primary_focus': focus,
        'daily_target': {
            'calories_kcal': target,
            'protein_g': protein_target,
            'carbs_g': carbs_target,
            'fat_g': fat_target,
        },
        'days': days,
        'prep_tips': [
            'Prepare one protein option and wash or chop vegetables ahead of time.',
            'Keep two quick meals available for busy days.',
            'Use familiar portion sizes, then log the foods you actually eat.',
        ],
        'shopping_list': [
            'Oats or another whole grain', 'Rice or whole-wheat chapati ingredients',
            'Dal, beans or chickpeas',
            ('Tofu, beans and fortified soy alternatives' if diet == 'vegan' else
             'Tofu, paneer, beans or lentils' if diet == 'vegetarian' else
             'Tofu, paneer, fish or legumes' if diet == 'pescatarian' else
             'Eggs, tofu, paneer, fish or chicken to match your diet'),
            ('Fortified soy yogurt or another suitable alternative' if diet == 'vegan' else 'Curd or yogurt'),
            'Seasonal vegetables and fruit', 'Seeds or another suitable snack option',
        ],
        'notes': 'This is a flexible planning aid, not medical advice. Meal calories and protein are approximate; adjust portions to match real food labels, hunger, activity and your registered target.',
    }


def _validate_plan(payload, profile, preferences, diary_summary):
    if not isinstance(payload, dict) or not isinstance(payload.get('days'), list) or len(payload['days']) != 7:
        raise ValueError('The generated plan did not contain seven days.')
    target = payload.get('daily_target')
    if not isinstance(target, dict):
        target = {}
    safe_target = {
        'calories_kcal': _bounded_number(target.get('calories_kcal'), getattr(profile, 'daily_calorie_goal', 2000), 500, 10000),
        'protein_g': _bounded_number(target.get('protein_g'), getattr(profile, 'daily_protein_goal', 120), 10, 600),
        'carbs_g': _bounded_number(target.get('carbs_g'), getattr(profile, 'daily_carbs_goal', 220), 10, 1000),
        'fat_g': _bounded_number(target.get('fat_g'), getattr(profile, 'daily_fat_goal', 65), 5, 500),
    }
    days = []
    for index, raw_day in enumerate(payload['days']):
        if not isinstance(raw_day, dict) or not isinstance(raw_day.get('meals'), list) or len(raw_day['meals']) < 3:
            raise ValueError(f'Day {index + 1} is missing meal information.')
        meals = []
        for raw_meal in raw_day['meals'][:5]:
            if not isinstance(raw_meal, dict):
                continue
            meals.append({
                'type': str(raw_meal.get('type', 'Meal'))[:32],
                'name': str(raw_meal.get('name', 'Balanced meal'))[:120],
                'description': str(raw_meal.get('description', 'Adjust portions to your needs.'))[:300],
                'calories_kcal': _bounded_number(raw_meal.get('calories_kcal'), 400, 0, 3000),
                'protein_g': _bounded_number(raw_meal.get('protein_g'), 20, 0, 250),
            })
        if len(meals) < 3:
            raise ValueError(f'Day {index + 1} did not contain three usable meals.')
        days.append({
            'day': str(raw_day.get('day') or DAY_NAMES[index])[:16],
            'focus': str(raw_day.get('focus', 'Keep it consistent'))[:120],
            'meals': meals,
            'movement': str(raw_day.get('movement', 'Choose comfortable movement or rest.'))[:300],
            'habit': str(raw_day.get('habit', 'Log what you eat.'))[:200],
        })
    def short_list(key, fallback):
        raw = payload.get(key)
        if not isinstance(raw, list):
            return fallback
        return [str(value)[:180] for value in raw[:12] if str(value).strip()]

    return {
        'title': str(payload.get('title', 'Your weekly plan'))[:100],
        'summary': str(payload.get('summary', 'A flexible plan matched to your current targets.'))[:500],
        'primary_focus': str(payload.get('primary_focus', 'Build consistent habits.'))[:500],
        'daily_target': safe_target,
        'days': days,
        'prep_tips': short_list('prep_tips', []),
        'shopping_list': short_list('shopping_list', []),
        'notes': str(payload.get('notes', 'Meal estimates are approximate.'))[:700],
    }


def _bounded_number(value, default, low, high):
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError, OverflowError):
        value = int(default or low)
    return max(low, min(high, value))


def _extract_json(text):
    text = (text or '').strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    start, end = text.find('{'), text.rfind('}')
    if start < 0 or end <= start:
        raise ValueError('No JSON object in AI response.')
    return json.loads(text[start:end + 1])


def generate_weekly_plan(profile, preferences, diary_summary=''):
    """Return (plan_data, source, user_safe_note). Never claims fallback content is AI-generated."""
    fallback = lambda: _fallback_plan(profile, preferences, diary_summary)
    def fallback_note(base):
        if str(preferences.get('foods_to_avoid', '')).strip():
            return base + ' This fallback cannot reliably enforce every food exclusion; inspect every ingredient carefully, especially if the exclusion is an allergy.'
        return base
    api_key = str(getattr(settings, 'AI_API_KEY', '') or '').strip()
    api_url = str(getattr(settings, 'AI_API_URL', '') or '').strip()
    model = str(getattr(settings, 'AI_MODEL', 'qwen/qwen3.8-27b') or 'qwen/qwen3.8-27b').strip()
    timeout = max(10, int(getattr(settings, 'AI_API_TIMEOUT', 35)))
    if not api_key or not api_url:
        note = fallback_note('AI is not configured in this environment, so a starter template was created instead.')
        return fallback(), 'template', note

    profile_context = (
        f"Daily target: {profile.daily_calorie_goal} kcal; protein: {profile.daily_protein_goal} g; "
        f"carbohydrates: {profile.daily_carbs_goal} g; fat: {profile.daily_fat_goal} g; "
        f"current weight: {profile.current_weight if profile.current_weight is not None else 'not set'} kg; "
        f"target weight: {profile.target_weight if profile.target_weight is not None else 'not set'} kg."
    )
    system_prompt = (
        "You are Fitora's thoughtful nutrition and habit-planning assistant. Generate a realistic, flexible 7-day meal and movement plan. "
        "Treat the user's current Fitora calorie and macro targets as the target, not a medical prescription. Do not infer age, height, sex, health conditions, allergies, or exact energy requirements when not provided. "
        "Never prescribe crash diets, excessive calorie restriction, supplements, or medical treatment. Respect dietary style and exclusions. "
        "Use practical foods suited to the selected budget, fit the selected cooking-time limit, and avoid unnecessary repetition. Treat 'high_protein' as a meal emphasis, not a dietary restriction. Respect the requested number of training days and food exclusions; if an exclusion might be an allergy, clearly remind the user to verify every ingredient. Include meals and one small habit for every day. Keep food calories and protein clearly approximate. "
        "Output ONLY a valid JSON object with this exact structure: "
        '{"title":"...","summary":"...","primary_focus":"...",'
        '"daily_target":{"calories_kcal":2000,"protein_g":120,"carbs_g":220,"fat_g":65},'
        '"days":[{"day":"Monday","focus":"...","meals":[{"type":"Breakfast","name":"...","description":"...","calories_kcal":450,"protein_g":25},'
        '{"type":"Lunch","name":"...","description":"...","calories_kcal":650,"protein_g":35},'
        '{"type":"Dinner","name":"...","description":"...","calories_kcal":600,"protein_g":35},'
        '{"type":"Snack","name":"...","description":"...","calories_kcal":200,"protein_g":10}],'
        '"movement":"...","habit":"..."}],'
        '"prep_tips":["..."],"shopping_list":["..."],"notes":"..."}. '
        "The days array must contain exactly Monday through Sunday in order. Return 3–4 meals per day. Keep the response concise and valid JSON, with no Markdown fence."
    )
    user_prompt = (
        f"User profile: {profile_context}\n"
        f"Preferences: {json.dumps(preferences, ensure_ascii=False)}\n"
        f"Recent diary summary based only on logged data: {diary_summary or 'No recent diary entries were logged.'}\n"
        "Create a plan that supports the stated goal without pretending logged food data is complete. Make portions flexible."
    )
    try:
        response = requests.post(
            api_url,
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': 0.25,
                'max_completion_tokens': 2300,
                'stream': False,
            },
            timeout=(5, timeout),
        )
        if response.status_code != 200:
            logger.warning('Weekly plan AI provider returned HTTP %s.', response.status_code)
            note = fallback_note('The AI provider did not return a usable plan, so a starter template was created.')
            return fallback(), 'template', note
        choices = response.json().get('choices') or []
        content = choices[0].get('message', {}).get('content', '') if choices else ''
        if isinstance(content, list):
            content = ''.join(item.get('text', '') for item in content if isinstance(item, dict))
        plan_data = _validate_plan(_extract_json(content), profile, preferences, diary_summary)
        return plan_data, 'ai', ''
    except requests.exceptions.Timeout:
        logger.warning('Weekly plan AI request timed out after %s seconds.', timeout)
        return fallback(), 'template', fallback_note('The AI request timed out, so a starter template was created. You can generate again later.')
    except requests.exceptions.RequestException as exc:
        logger.warning('Weekly plan AI transport error (%s).', exc.__class__.__name__)
        return fallback(), 'template', fallback_note('The AI service could not be reached, so a starter template was created.')
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        logger.warning('Weekly plan AI response was unusable (%s).', exc.__class__.__name__)
        return fallback(), 'template', fallback_note('The AI response was not in the expected format, so a starter template was created.')
