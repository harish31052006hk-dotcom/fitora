from django.contrib import admin
from .models import FAQ, SupportTicket

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'order', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('is_active', 'order')

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'subject', 'category', 'status', 'user', 'contact_email', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('ticket_id', 'subject', 'description', 'user__username', 'contact_email')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
