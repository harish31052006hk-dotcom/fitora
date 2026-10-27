from django.core.management.base import BaseCommand
from support.models import FAQ

INITIAL_FAQS = [
    {
        'question': 'How do I create an account?',
        'answer': 'Click on "Sign Up" or "Get Started" in the navigation bar. Enter a unique username, your email address, and a secure password (minimum 8 characters). Once submitted, your personal account and nutrition profile are immediately initialized.',
        'category': 'Getting Started',
        'order': 1
    },
    {
        'question': 'How do I set my calorie goal?',
        'answer': 'Navigate to your Profile via the top right navigation menu. In the "Nutrition Goals" section, enter your target daily calorie intake in kcal (e.g., 2000 kcal). You can also configure your daily targets for protein, carbohydrates, and fat.',
        'category': 'Nutrition & Goals',
        'order': 2
    },
    {
        'question': 'How do I add food to my diary?',
        'answer': 'Go to the Food Diary page, choose a meal category (Breakfast, Lunch, Dinner, or Snacks), and click "+ Add Food". You can either search our verified nutrition database or enter custom food details with your serving size in grams or units.',
        'category': 'Food Diary',
        'order': 3
    },
    {
        'question': 'How are daily calories calculated?',
        'answer': 'Fitora calculates daily calories using precision Decimal arithmetic: Calories Remaining = Daily Calorie Goal - Calories Consumed. Calories consumed is the exact sum of all food entries logged for that specific date.',
        'category': 'Food Diary',
        'order': 4
    },
    {
        'question': 'How do I track protein?',
        'answer': 'Each food logged tracks grams of protein. Your dashboard and food diary display your daily protein progress bar against your personal protein goal. 1 gram of protein provides approximately 4 kcal of energy.',
        'category': 'Nutrition & Goals',
        'order': 5
    },
    {
        'question': 'How do I edit a food entry?',
        'answer': 'In your Food Diary for any given day, locate the entry you wish to modify. Click the edit (pencil) icon next to the food item. Update the serving amount or macronutrient quantities and click "Save Changes".',
        'category': 'Food Diary',
        'order': 6
    },
    {
        'question': 'How do I create a recipe?',
        'answer': 'Visit "Recipes" in the navigation bar and click "+ Create Recipe". Enter the recipe name, portion count (servings), and add each ingredient with its quantity. Fitora automatically calculates total calories as well as per-serving macronutrients.',
        'category': 'Recipes',
        'order': 7
    },
    {
        'question': 'How do I record my weight?',
        'answer': 'Go to the "Progress" page from the navigation bar. Under the "Log Weight Measurement" section, enter the date, your weight in kilograms (kg), and any optional notes. Fitora charts your historical weight trend over time.',
        'category': 'Nutrition & Goals',
        'order': 8
    },
    {
        'question': 'How do I view my progress?',
        'answer': 'Navigate to the "Progress" page to see interactive Chart.js visualizations. You can inspect your 7-day calorie balance against your goal, weekly macronutrient breakdown (protein, carbs, fat split), and weight history.',
        'category': 'Nutrition & Goals',
        'order': 9
    },
    {
        'question': 'Why is food search unavailable?',
        'answer': 'If external third-party nutrition services experience network delays or downtime, Fitora triggers an automated fallback to our verified local PostgreSQL database. You can also create and use Custom Foods anytime.',
        'category': 'Technical & Account',
        'order': 10
    },
    {
        'question': 'How do I reset my password?',
        'answer': 'If you forget your password, you can contact support or an administrator to reset your credentials. When logged in, you can update your security details under your account profile settings.',
        'category': 'Technical & Account',
        'order': 11
    },
    {
        'question': 'How do I contact support?',
        'answer': 'You can submit a ticket on our "Help & Support" page or ask the floating Fitora AI assistant. When technical assistance is required, the AI can automatically generate a tracked support ticket with a unique ticket reference ID.',
        'category': 'Technical & Account',
        'order': 12
    },
    {
        'question': 'What does error code APP-001 mean?',
        'answer': 'APP-001 is a Fitora application-specific code indicating a local nutrition calculation issue or external API fallback. It occurs when nutrition values exceed safe numeric boundaries or external nutrition search fails and defaults to saved database foods.',
        'category': 'Technical & Account',
        'order': 13
    }
]

class Command(BaseCommand):
    help = 'Seeds initial 12+ FAQ records into PostgreSQL database'

    def handle(self, *args, **options):
        count = 0
        for data in INITIAL_FAQS:
            faq, created = FAQ.objects.get_or_create(
                question=data['question'],
                defaults=data
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} FAQ entries into PostgreSQL."))
