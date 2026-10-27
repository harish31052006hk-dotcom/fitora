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
]
