from django.urls import path

from . import views

app_name = 'remover'

urlpatterns = [
    path('', views.home, name='home'),
    path('result/<int:pk>/', views.result, name='result'),
    path('result/<int:pk>/download/', views.download, name='download'),
    path('history/', views.history, name='history'),
]
