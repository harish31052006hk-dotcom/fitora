"""
URL configuration for Fitora project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import support.views as support_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('diary/', include('food_diary.urls')),
    path('nutrition/', include('nutrition.urls')),
    path('recipes/', include('recipes.urls')),
    path('progress/', include('progress.urls')),
    path('assistant/', include('assistant.urls')),
    path('plan/', include('plans.urls')),
    path('support/', include('support.urls')),
    path('health/', support_views.health_check_view, name='root_health_check'),
    path('faq/', support_views.faq_view, name='root_faq'),
    path('errors/', support_views.error_guide_view, name='root_errors'),
]

# Custom HTTP Error Handlers
handler404 = 'support.views.custom_404_view'
handler500 = 'support.views.custom_500_view'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
