from django.conf import settings
from django.db import models

from chapters.models import Chapter


class Comment(models.Model):
    """Comentario de un usuario en un capítulo específico. Soporta respuestas anidadas (1 nivel)."""

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField(max_length=1000)
    
    # Nuevo: permite vincular un comentario a un párrafo específico del capítulo
    paragraph_index = models.PositiveIntegerField(null=True, blank=True, help_text='Índice del párrafo al que pertenece (0, 1, 2...)')
    
    created_at = models.DateTimeField(auto_now_add=True)

    # Respuestas anidadas: si parent es None, es un comentario raíz
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )

    # Moderación básica: permite ocultar sin borrar (útil para apelaciones)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author} en {self.chapter}'

    @property
    def likes_count(self):
        return self.likes.count()


class CommentLike(models.Model):
    """Like de un usuario a un comentario. Cada usuario solo puede dar un like por comentario."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} ❤️ comentario {self.comment.id}"
