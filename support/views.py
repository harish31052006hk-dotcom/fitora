import sys
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import connection
from django.utils import timezone
from django.conf import settings

from .models import FAQ, SupportTicket
from .forms import SupportTicketForm
from .error_data import ERROR_CODES

def faq_view(request):
    """
    Renders PostgreSQL-backed FAQ knowledge base with search and category filtering.
    """
    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()

    faqs = FAQ.objects.filter(is_active=True)

    if search_query:
        faqs = faqs.filter(question__icontains=search_query) | faqs.filter(answer__icontains=search_query)

    if selected_category and selected_category != 'All':
        faqs = faqs.filter(category=selected_category)

    # Get list of categories
    categories = ['All'] + list(FAQ.objects.filter(is_active=True).values_list('category', flat=True).distinct())

    return render(request, 'support/faq.html', {
        'faqs': faqs,
        'categories': categories,
        'selected_category': selected_category or 'All',
        'search_query': search_query,
        'faq_count': faqs.count(),
        'title': 'Frequently Asked Questions & Help'
    })

def error_guide_view(request):
    """
    Comprehensive error documentation for all 8 documented codes
    (7 HTTP codes + 1 custom APP-001 code).
    """
    return render(request, 'support/error_guide.html', {
        'error_codes': ERROR_CODES,
        'title': 'Error Code Documentation & Troubleshooting Guide'
    })

def support_tickets_view(request):
    """
    Support ticket management portal.
    Users can submit a ticket, get an assigned ID, and view their past tickets.
    """
    if request.user.is_authenticated:
        user_tickets = SupportTicket.objects.filter(user=request.user)
    else:
        user_tickets = []

    if request.method == 'POST':
        form = SupportTicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
                if not ticket.contact_email:
                    ticket.contact_email = request.user.email
            ticket.ticket_id = SupportTicket.generate_ticket_id()
            ticket.save()
            messages.success(
                request,
                f"Support ticket successfully submitted! Your Ticket Reference ID is: {ticket.ticket_id}"
            )
            return redirect('support_tickets')
        else:
            messages.error(request, "Please check the form fields and try again.")
    else:
        form = SupportTicketForm(user=request.user)

    return render(request, 'support/tickets.html', {
        'form': form,
        'user_tickets': user_tickets,
        'title': 'Help Desk & Support Tickets'
    })

@login_required
def ticket_detail_view(request, ticket_id):
    """
    Displays single ticket detail. Strict user isolation.
    """
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id, user=request.user)
    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'title': f"Ticket {ticket.ticket_id}"
    })

def health_check_view(request):
    """
    Monitoring and health check endpoint at /health/.
    Returns structured JSON with PostgreSQL connectivity, system latency, and app status.
    """
    start_time = time.perf_counter()
    health_status = {
        'status': 'healthy',
        'app': 'Fitora',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    http_status = 200

    # 1. Check Relational Database (PostgreSQL / SQLite fallback)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        health_status['services']['relational_database'] = {
            'status': 'connected',
            'engine': connection.vendor
        }
    except Exception:
        health_status['status'] = 'degraded'
        health_status['services']['relational_database'] = {
            'status': 'unreachable',
            'engine': connection.vendor
        }
        http_status = 503

    # 2. Check MongoDB Connectivity
    from assistant.mongo_client import check_mongo_health
    mongo_ok = check_mongo_health()
    health_status['services']['mongodb_atlas'] = {
        'status': 'connected' if mongo_ok else 'offline_or_not_configured'
    }

    # 3. Nutrition API Status
    nutrition_api_configured = bool(getattr(settings, 'NUTRITION_API_KEY', None))
    health_status['services']['nutrition_api'] = {
        'status': 'active',
        'provider': 'Open Food Facts / Nutrition API',
        'custom_key_configured': nutrition_api_configured
    }

    # 4. AI Service Status
    ai_key_configured = bool(getattr(settings, 'AI_API_KEY', None))
    health_status['services']['ai_assistant'] = {
        'status': 'active' if ai_key_configured else 'fallback_mode_enabled',
        'api_configured': ai_key_configured
    }

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    health_status['response_time_ms'] = latency_ms

    return JsonResponse(health_status, status=http_status)

def app001_demo_view(request):
    """
    Demonstration endpoint for testing application-specific code APP-001.
    """
    return render(request, 'support/app001_notice.html', {
        'code': 'APP-001',
        'title': 'Fitora Application Event (APP-001)',
        'message': 'A demonstration of the Fitora application-specific error handling protocol (APP-001).',
        'details': ERROR_CODES['APP-001']
    })

def custom_404_view(request, exception=None):
    """
    Branded custom 404 page handler.
    """
    return render(request, '404.html', {'title': 'Page Not Found — Fitora'}, status=404)

def custom_500_view(request):
    """
    Branded custom 500 internal server error page handler.
    """
    return render(request, '500.html', {'title': 'Server Error — Fitora'}, status=500)
