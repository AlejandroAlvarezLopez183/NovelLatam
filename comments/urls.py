from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    path('like/<int:comment_id>/', views.toggle_like, name='toggle_like'),
    path('delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]
