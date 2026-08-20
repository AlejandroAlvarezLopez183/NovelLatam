from django.contrib import admin

from .models import Chapter


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('novel', 'order', 'title', 'is_published', 'publish_at')
    list_filter = ('is_published', 'novel')
    search_fields = ('title', 'novel__title')
    ordering = ('novel', 'order')
