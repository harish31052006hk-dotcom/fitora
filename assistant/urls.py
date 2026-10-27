from django.urls import path
from . import views

urlpatterns = [
    path('', views.assistant_page_view, name='assistant_page'),
    path('api/chat/', views.chat_api_view, name='assistant_chat_api'),
    path('api/feedback/', views.feedback_api_view, name='assistant_feedback_api'),
]
