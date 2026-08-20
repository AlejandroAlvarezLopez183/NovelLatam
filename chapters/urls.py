from django.urls import path

from . import views

app_name = 'chapters'

urlpatterns = [
    # /novela/<slug>/capitulo/<order>/
    path(
        'novela/<slug:novel_slug>/capitulo/<int:chapter_order>/',
        views.chapter_read,
        name='read',
    ),
    # Editor
    path('novela/<slug:novel_slug>/nuevo-capitulo/', views.chapter_create, name='create'),
    path('novela/<slug:novel_slug>/capitulo/<int:chapter_order>/editar/', views.chapter_update, name='update'),
    # HTMX: POST para crear comentario
    path(
        'capitulo/<int:chapter_id>/comentar/',
        views.comment_create,
        name='comment_create',
    ),
    # HTMX: Cargar comentarios por párrafo
    path(
        'capitulo/<int:chapter_id>/parrafo/<int:paragraph_index>/comentarios/',
        views.paragraph_comments,
        name='paragraph_comments',
    ),
]
