from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('<int:notification_id>/leer/', views.mark_read_and_redirect, name='mark_read'),
]
