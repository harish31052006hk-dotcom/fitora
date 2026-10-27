from django.urls import path
from . import views

urlpatterns = [
    path('', views.diary_view, name='food_diary'),
    path('add/', views.add_entry_view, name='add_entry'),
    path('edit/<int:entry_id>/', views.edit_entry_view, name='edit_entry'),
    path('delete/<int:entry_id>/', views.delete_entry_view, name='delete_entry'),
]
