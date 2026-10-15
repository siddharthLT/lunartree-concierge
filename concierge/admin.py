from django.contrib import admin

from .models import ConciergeRequest, Visitor


@admin.register(ConciergeRequest)
class ConciergeRequestAdmin(admin.ModelAdmin):
    list_display = ('request_type', 'guest_name', 'email', 'organization', 'status', 'created_at')
    list_filter = ('request_type', 'status')
    search_fields = ('guest_name', 'email', 'organization')
    ordering = ('-created_at',)


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'segment', 'completed', 'updated_at')
    list_filter = ('completed', 'segment')
    search_fields = ('name', 'company', 'email')
