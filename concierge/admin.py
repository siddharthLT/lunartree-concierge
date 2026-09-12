from django.contrib import admin

from .models import ConciergeRequest


@admin.register(ConciergeRequest)
class ConciergeRequestAdmin(admin.ModelAdmin):
    list_display = ('request_type', 'guest_name', 'email', 'organization', 'status', 'created_at')
    list_filter = ('request_type', 'status')
    search_fields = ('guest_name', 'email', 'organization')
    ordering = ('-created_at',)
