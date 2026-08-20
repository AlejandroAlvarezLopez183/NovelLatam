from django.conf import settings
from django.db import models


class Report(models.Model):
    """Reporte de un usuario sobre contenido problemático (novela, capítulo o comentario)."""

    class ContentType(models.TextChoices):
        NOVEL = 'novel', 'Novela'
        CHAPTER = 'chapter', 'Capítulo'
        COMMENT = 'comment', 'Comentario'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        REVIEWED = 'reviewed', 'Revisado'
        DISMISSED = 'dismissed', 'Descartado'

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    object_id = models.PositiveIntegerField(help_text='ID del objeto reportado (novela/capítulo/comentario)')
    reason = models.TextField(max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Reporte #{self.pk} — {self.get_content_type_display()} ({self.get_status_display()})'
