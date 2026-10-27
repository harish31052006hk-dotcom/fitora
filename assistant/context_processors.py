from datetime import datetime

def fitora_globals(request):
    """
    Provides global template context variables for Fitora.
    """
    return {
        'APP_NAME': 'Fitora',
        'APP_TAGLINE': 'Your Goals. Your Journey. Your Fit.',
        'CURRENT_YEAR': datetime.now().year,
    }
