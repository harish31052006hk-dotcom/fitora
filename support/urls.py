from django.urls import path
from . import views

urlpatterns = [
    path('faq/', views.faq_view, name='faq'),
    path('errors/', views.error_guide_view, name='error_guide'),
    path('tickets/', views.support_tickets_view, name='support_tickets'),
    path('tickets/<str:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),
    path('health/', views.health_check_view, name='health_check'),
    path('demo-app001/', views.app001_demo_view, name='demo_app001'),
]
