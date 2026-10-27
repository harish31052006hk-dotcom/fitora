from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipe_list_view, name='recipe_list'),
    path('create/', views.create_recipe_view, name='create_recipe'),
    path('<int:recipe_id>/', views.recipe_detail_view, name='recipe_detail'),
    path('<int:recipe_id>/edit/', views.edit_recipe_view, name='edit_recipe'),
    path('<int:recipe_id>/delete/', views.delete_recipe_view, name='delete_recipe'),
    path('<int:recipe_id>/ingredient/<int:ingredient_id>/delete/', views.delete_ingredient_view, name='delete_ingredient'),
    path('<int:recipe_id>/log/', views.log_recipe_to_diary, name='log_recipe_to_diary'),

    # Saved Meals
    path('saved-meals/', views.saved_meals_list_view, name='saved_meals_list'),
    path('saved-meals/create/', views.create_saved_meal_view, name='create_saved_meal'),
    path('saved-meals/<int:meal_id>/', views.saved_meal_detail_view, name='saved_meal_detail'),
    path('saved-meals/<int:meal_id>/edit/', views.edit_saved_meal_view, name='edit_saved_meal'),
    path('saved-meals/<int:meal_id>/delete/', views.delete_saved_meal_view, name='delete_saved_meal'),
    path('saved-meals/<int:meal_id>/item/<int:item_id>/delete/', views.delete_saved_meal_item_view, name='delete_saved_meal_item'),
    path('saved-meals/<int:meal_id>/log/', views.log_saved_meal_to_diary_view, name='log_saved_meal_to_diary'),
]
