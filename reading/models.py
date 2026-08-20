from django.conf import settings
from django.db import models
from chapters.models import Chapter
from novels.models import Novel


class Bookmark(models.Model):
    """Guarda una novela en la biblioteca del usuario y rastrea el último capítulo leído."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='bookmarked_by')
    last_read_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'novel')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} -> {self.novel.title}"


class ReadingProgress(models.Model):
    """Registra que un usuario leyó un capítulo específico (un registro por capítulo leído)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='readers')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'chapter')
        ordering = ['-read_at']

    def __str__(self):
        return f"{self.user.username} leyó {self.chapter}"


class AuthorFollow(models.Model):
    """Un usuario sigue a un autor para recibir notificaciones de nuevos capítulos."""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'author')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} sigue a {self.author.username}"


class AuthorSupport(models.Model):
    """Un lector apoya a un autor con un 'me gusta' (uno por par usuario/autor)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supports_given',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supports_received',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'author')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} apoyó a {self.author.username}"
