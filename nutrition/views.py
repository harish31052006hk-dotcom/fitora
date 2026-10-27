from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import FoodItem
from .forms import CustomFoodForm
from .api_client import NutritionAPIClient

def search_foods_api(request):
    """
    JSON API endpoint for food search supporting case-insensitive partial matching.
    Searches the existing PostgreSQL food database and external nutrition service.
    """
    query = (request.GET.get('query') or request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({
            'success': True,
            'source': 'empty',
            'message': 'Please enter a search query.',
            'items': [],
            'results': []
        })

    client = NutritionAPIClient()
    result = client.search_food(query, user=request.user)

    # Fetch matching PostgreSQL database items
    db_items = client._fetch_from_database(query, user=request.user)

    # Combine items giving priority to PostgreSQL database records
    seen_keys = set()
    combined_items = []

    for item in db_items:
        key = (item.get('name', '').strip().lower(), item.get('brand', '').strip().lower())
        if key not in seen_keys:
            seen_keys.add(key)
            combined_items.append(item)

    for item in result.get('items', []):
        key = (item.get('name', '').strip().lower(), item.get('brand', '').strip().lower())
        if key not in seen_keys:
            seen_keys.add(key)
            combined_items.append(item)

    formatted_items = []
    for item in combined_items:
        formatted_items.append({
            'id': item.get('id'),
            'name': item.get('name'),
            'brand': item.get('brand', ''),
            'serving_description': item.get('serving_description', ''),
            'serving_size': float(item.get('serving_size', 100)),
            'serving_unit': item.get('serving_unit', 'g'),
            'calories': float(item.get('calories', 0)),
            'protein': float(item.get('protein', 0)),
            'carbohydrates': float(item.get('carbohydrates', 0)),
            'fat': float(item.get('fat', 0)),
            'source': item.get('source', ''),
            'is_verified': item.get('is_verified', False)
        })

    return JsonResponse({
        'success': True,
        'source': 'database' if db_items else result.get('source', 'api'),
        'message': f"Found {len(formatted_items)} matching foods in database.",
        'is_fallback': result.get('is_fallback', False),
        'items': formatted_items,
        'results': formatted_items
    })

@login_required
def custom_foods_view(request):
    """
    Lists custom foods created by user and handles new custom food creation.
    """
    custom_foods = FoodItem.objects.filter(created_by=request.user)
    
    if request.method == 'POST':
        form = CustomFoodForm(request.POST)
        if form.is_valid():
            food = form.save(commit=False)
            food.created_by = request.user
            food.is_verified = False
            food.data_source = 'Custom User Food'
            food.save()
            messages.success(request, f"'{food.name}' was saved to your custom foods!")
            return redirect('custom_foods')
        else:
            messages.error(request, "Please correct the errors in the custom food form.")
    else:
        form = CustomFoodForm()
        
    return render(request, 'nutrition/custom_foods.html', {
        'form': form,
        'custom_foods': custom_foods,
        'title': 'Custom Food Database'
    })

@login_required
def delete_custom_food(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id, created_by=request.user)
    if request.method == 'POST':
        name = food.name
        food.delete()
        messages.success(request, f"Custom food '{name}' deleted.")
    return redirect('custom_foods')
