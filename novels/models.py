from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Novel(models.Model):
    """Una novela publicada por un autor."""

    class Genre(models.TextChoices):
        ISEKAI = 'isekai', 'Isekai'
        FANTASY_YA = 'fantasy_ya', 'Fantasía juvenil'
        LITRPG = 'litrpg', 'LitRPG / Progression'
        ADVENTURE = 'adventure', 'Aventura'
        LIGHT_NOVEL = 'light_novel', 'Novela ligera'

    class Rating(models.TextChoices):
        ALL_AGES = 'all_ages', 'Todo público'
        TEEN = 'teen', 'Juvenil (13+)'
        MATURE_TEEN = 'mature_teen', 'Juvenil mayor (16+)'

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='novels')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    synopsis = models.TextField(max_length=2000)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    genre = models.CharField(max_length=20, choices=Genre.choices)
    rating = models.CharField(max_length=20, choices=Rating.choices, default=Rating.TEEN)

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Review(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('novel', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.novel.title} ({self.rating}/5)"
