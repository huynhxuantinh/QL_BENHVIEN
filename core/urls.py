from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('benh-vien/<int:id>/', views.hospital_detail, name='hospital_detail'),
    path("dat-lich/", views.dat_lich, name="dat_lich"),
        path("login/", views.user_login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path("dat-lich/<int:bv_id>/", views.dat_lich, name="dat_lich"),

]