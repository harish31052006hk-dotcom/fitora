from django.urls import path
from . import views

urlpatterns = [
    path('api/search/', views.search_foods_api, name='food_search_api'),
    path('custom-foods/', views.custom_foods_view, name='custom_foods'),
    path('custom-foods/<int:food_id>/delete/', views.delete_custom_food, name='delete_custom_food'),
]
