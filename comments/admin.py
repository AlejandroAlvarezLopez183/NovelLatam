from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'chapter', 'created_at', 'is_hidden')
    list_filter = ('is_hidden',)
    search_fields = ('body', 'author__username')
    actions = ['hide_comments', 'unhide_comments']

    @admin.action(description='Ocultar comentarios seleccionados')
    def hide_comments(self, request, queryset):
        queryset.update(is_hidden=True)

    @admin.action(description='Volver a mostrar comentarios seleccionados')
    def unhide_comments(self, request, queryset):
        queryset.update(is_hidden=False)
