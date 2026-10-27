import logging
import requests
from decimal import Decimal
from django.conf import settings
from .models import FoodItem

logger = logging.getLogger('fitora.nutrition')

class NutritionAPIClient:
    """
    Robust client for querying third-party nutrition data with connection timeouts,
    rate-limit handling, exception resilience, and local database fallback.
    """
    OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"

    def __init__(self):
        self.timeout = getattr(settings, 'NUTRITION_API_TIMEOUT', 4)
        self.api_key = getattr(settings, 'NUTRITION_API_KEY', '')

    def search_food(self, query, user=None):
        """
        Searches nutrition data via external API with fallback to local database.
        Returns a dict with: items, source ('api' or 'fallback'), message, is_fallback.
        """
        query = query.strip()
        if not query:
            return {
                'success': True,
                'source': 'empty',
                'items': [],
                'message': 'Please enter a search term.',
                'is_fallback': False
            }

        # Attempt external API query with timeout & error handling
        api_items = self._fetch_from_api(query)
        if api_items is not None:
            return {
                'success': True,
                'source': 'api',
                'items': api_items,
                'message': f"Found {len(api_items)} verified results from nutrition service.",
                'is_fallback': False
            }

        # Fallback to local verified and user-saved database items
        logger.warning(f"External nutrition API unavailable for query '{query}'. Activating local database fallback.")
        fallback_items = self._fetch_from_database(query, user)
        return {
            'success': True,
            'source': 'fallback',
            'items': fallback_items,
            'message': "External nutrition service is currently unavailable or timed out. Showing verified database foods.",
            'is_fallback': True
        }

    def _fetch_from_api(self, query):
        """
        Fetches products from Open Food Facts API with strict timeout and status handling.
        """
        params = {
            'search_terms': query,
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 10,
        }
        headers = {
            'User-Agent': 'Fitora-NutritionApp/1.0 (academic assessment project; contact@fitora.local)'
        }
        
        try:
            response = requests.get(
                self.OPEN_FOOD_FACTS_URL,
                params=params,
                headers=headers,
                timeout=(2.5, self.timeout)
            )

            if response.status_code == 429:
                logger.warning("Nutrition API returned HTTP 429: Too Many Requests.")
                return None
            elif response.status_code != 200:
                logger.warning(f"Nutrition API returned status code {response.status_code}.")
                return None

            data = response.json()
            products = data.get('products', [])
            items = []

            for p in products:
                name = p.get('product_name')
                if not name:
                    continue

                nutriments = p.get('nutriments', {})
                # Extract calories (energy-kcal_100g or energy-kcal)
                kcal = nutriments.get('energy-kcal_100g') or nutriments.get('energy-kcal') or 0
                protein = nutriments.get('proteins_100g') or nutriments.get('proteins') or 0
                carbs = nutriments.get('carbohydrates_100g') or nutriments.get('carbohydrates') or 0
                fat = nutriments.get('fat_100g') or nutriments.get('fat') or 0

                try:
                    items.append({
                        'id': None,
                        'name': str(name)[:180],
                        'brand': str(p.get('brands', ''))[:100],
                        'serving_size': Decimal('100.00'),
                        'serving_unit': 'g',
                        'calories': Decimal(str(round(float(kcal), 2))),
                        'protein': Decimal(str(round(float(protein), 2))),
                        'carbohydrates': Decimal(str(round(float(carbs), 2))),
                        'fat': Decimal(str(round(float(fat), 2))),
                        'source': 'External API (Open Food Facts)',
                        'is_verified': True
                    })
                except (ValueError, TypeError):
                    continue

            return items

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout occurred connecting to nutrition API after {self.timeout}s.")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error querying nutrition API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing nutrition API: {str(e)}")
            return None

    def _fetch_from_database(self, query, user=None):
        """
        Retrieves matching items from PostgreSQL database.
        """
        queryset = FoodItem.objects.filter(name__icontains=query)
        if user and user.is_authenticated:
            queryset = queryset.filter(models_q(is_verified=True) | models_q(created_by=user))
        else:
            queryset = queryset.filter(is_verified=True)

        results = []
        for item in queryset[:15]:
            results.append({
                'id': item.id,
                'name': item.name,
                'brand': item.brand,
                'serving_size': item.serving_size,
                'serving_unit': item.serving_unit,
                'calories': item.calories,
                'protein': item.protein,
                'carbohydrates': item.carbohydrates,
                'fat': item.fat,
                'source': 'Fitora Verified Database' if item.is_verified else 'Custom Food',
                'is_verified': item.is_verified
            })
        return results

def models_q(**kwargs):
    from django.db.models import Q
    return Q(**kwargs)
