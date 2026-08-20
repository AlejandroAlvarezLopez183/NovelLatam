from django.urls import path

from . import views

app_name = 'novels'

urlpatterns = [
    path('', views.home, name='home'),                              # Landing / home
    path('explorar/', views.novel_list, name='list'),               # Catálogo completo
    path('ranking/', views.ranking_view, name='ranking'),           # Leaderboard
    path('buscar-rapido/', views.quick_search, name='quick_search'),
    path('novela/<slug:slug>/', views.novel_detail, name='detail'),
    path('novela/<slug:slug>/editar/', views.novel_update, name='update'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('nueva/', views.novel_create, name='create'),
]
