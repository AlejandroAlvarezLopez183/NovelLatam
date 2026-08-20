from django.contrib import admin

from .models import Novel


@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'rating', 'is_published', 'updated_at')
    list_filter = ('genre', 'rating', 'is_published')
    search_fields = ('title', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
