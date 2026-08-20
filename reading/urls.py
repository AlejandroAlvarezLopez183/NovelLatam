from django.urls import path
from . import views

app_name = 'reading'

urlpatterns = [
    path('', views.library_view, name='library'),
    path('toggle/<slug:novel_slug>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('seguir/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('apoyar/<str:username>/', views.toggle_support, name='toggle_support'),
]
