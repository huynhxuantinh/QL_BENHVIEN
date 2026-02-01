from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('benh-vien/<int:id>/', views.hospital_detail, name='hospital_detail'),
]