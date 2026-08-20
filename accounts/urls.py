from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('registro/', views.register_view, name='register'),
    path('entrar/', views.login_view, name='login'),
    path('salir/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('editar/', views.edit_profile_view, name='edit_profile'),
    path('panel-autor/', views.author_dashboard_view, name='author_dashboard'),
    path('bloqueados/', views.blocked_users_view, name='blocked_users'),
    path('autor/<str:username>/', views.author_profile_view, name='author_profile'),
    path('bloquear/<str:username>/', views.toggle_block, name='toggle_block'),
    path('muro/publicar/', views.post_to_wall, name='post_to_wall'),
]
