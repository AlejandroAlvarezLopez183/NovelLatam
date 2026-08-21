from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


COUNTRY_CHOICES = [
    ('GLOBAL', 'Tierra (Global)'),
    ('AR', 'Argentina'),
    ('BO', 'Bolivia'),
    ('CL', 'Chile'),
    ('CO', 'Colombia'),
    ('CR', 'Costa Rica'),
    ('CU', 'Cuba'),
    ('EC', 'Ecuador'),
    ('SV', 'El Salvador'),
    ('ES', 'España'),
    ('GT', 'Guatemala'),
    ('HN', 'Honduras'),
    ('MX', 'México'),
    ('NI', 'Nicaragua'),
    ('PA', 'Panamá'),
    ('PY', 'Paraguay'),
    ('PE', 'Perú'),
    ('PR', 'Puerto Rico'),
    ('DO', 'República Dominicana'),
    ('UY', 'Uruguay'),
    ('VE', 'Venezuela'),
    ('US', 'Estados Unidos (Habla Hispana)'),
]


class UserProfile(models.Model):
    """Perfil extendido del usuario: bio, avatar y website."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text='Cuéntale algo a la comunidad sobre ti (máx. 500 caracteres)',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Foto de perfil (recomendado: cuadrada, mínimo 200×200 px)',
    )
    cover_photo = models.ImageField(
        upload_to='covers/',
        blank=True,
        null=True,
        help_text='Foto de portada para tu perfil (recomendado: 1200x400 px)',
    )
    website = models.URLField(
        max_length=200,
        blank=True,
        help_text='Tu blog, Twitter, Wattpad, etc.',
    )
    country = models.CharField(
        max_length=10,
        choices=COUNTRY_CHOICES,
        default='GLOBAL',
        help_text='Selecciona tu país para participar en los Rankings Nacionales.',
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un UserProfile cada vez que se registra un usuario."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


class UserBlock(models.Model):
    """Permite a un usuario bloquear a otro.
    El usuario bloqueador no verá los comentarios/reseñas del bloqueado,
    y el bloqueado no podrá interactuar con el bloqueador.
    """
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blocker.username} bloqueó a {self.blocked.username}"


class ProfileWallPost(models.Model):
    """Publicación en el muro de un usuario. Ideal para que los autores den anuncios."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wall_posts'
    )
    content = models.TextField(
        max_length=1000,
        help_text="Mensaje para tus seguidores y visitantes."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post de {self.author.username} el {self.created_at.strftime('%Y-%m-%d')}"
