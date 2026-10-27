from django.contrib import admin
from .models import WeightLog

@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'created_at')
    list_filter = ('date',)
    search_fields = ('user__username', 'notes')
