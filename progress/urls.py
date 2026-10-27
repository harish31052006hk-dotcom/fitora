from django.urls import path
from . import views

urlpatterns = [
    path('', views.progress_view, name='progress'),
    path('edit/<int:log_id>/', views.edit_weight_view, name='edit_weight'),
    path('delete/<int:log_id>/', views.delete_weight_view, name='delete_weight'),
]
