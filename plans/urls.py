from django.urls import path
from . import views

urlpatterns = [
    path('', views.weekly_plan_view, name='weekly_plan'),
]
