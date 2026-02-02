from django.urls import path
from . import views

urlpatterns = [

    # Trang chủ
    path("", views.home, name="home"),

    # Chi tiết bệnh viện
    path("benh-vien/<int:id>/", views.hospital_detail, name="hospital_detail"),

    # Đặt lịch theo bệnh viện
    path("dat-lich/<int:bv_id>/", views.dat_lich, name="dat_lich"),

    # Auth
    path("login/", views.user_login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path("bac-si/kham/<int:lich_id>/", views.doctor_exam, name="doctor_exam"),
    path("bac-si/", views.bac_si_home, name="bac_si_home"),
    path("profile/", views.profile, name="profile"),

]
