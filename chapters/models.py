from django.db import models

from novels.models import Novel


class Chapter(models.Model):
    """Un capítulo dentro de una novela."""

    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(help_text='Orden de lectura dentro de la novela')

    is_published = models.BooleanField(default=False)
    followers_only = models.BooleanField(
        default=False,
        help_text='Si está activado, solo los seguidores del autor pueden leer este capítulo',
    )
    publish_at = models.DateTimeField(
        blank=True, null=True,
        help_text='Programar publicación futura (dejar vacío para publicar ya)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['novel', 'order']
        unique_together = ('novel', 'order')

    def __str__(self):
        return f'{self.novel.title} — Cap. {self.order}: {self.title}'
