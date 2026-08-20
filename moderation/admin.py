from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'reported_by', 'status', 'created_at')
    list_filter = ('status', 'content_type')
    search_fields = ('reason',)
