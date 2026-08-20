"""
URL configuration for config project.

Cada app tiene su propio urls.py (accounts/urls.py, novels/urls.py, etc.)
y aquí solo las conectamos con un prefijo + namespace. Así el proyecto
se mantiene organizado conforme crece, sin amontonar todo aquí.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('novels.urls')),           # home = explorar novelas + detalle de novela
    path('', include('chapters.urls')),         # lectura de capítulos + comentarios HTMX
    path('cuenta/', include('accounts.urls')),
    path('notificaciones/', include('notifications.urls')),
    path('biblioteca/', include('reading.urls')),
    path('comentarios/', include('comments.urls')),  # likes de comentarios
]


# Servir archivos subidos (portadas, avatares) en desarrollo.
# En producción esto lo debe manejar Cloudflare R2/S3 + el servidor web, no Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
