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
    path("quen-mat-khau/", views.forgot_password, name="forgot_password"),
    path("thong-bao/", views.notifications, name="notifications"),
    path("lich-kham-sap-toi/", views.upcoming_appointments, name="upcoming_appointments"),
    path("lich-kham/<int:lich_id>/huy/", views.cancel_appointment, name="cancel_appointment"),
    path("lich-su-kham/", views.medical_history, name="medical_history"),
    path("phieu-kham/<int:phieu_id>/", views.phieu_kham_detail, name="phieu_kham_detail"),
    path("bac-si/kham/<int:lich_id>/", views.doctor_exam, name="doctor_exam"),
    path("bac-si/", views.bac_si_home, name="bac_si_home"),
    path("profile/", views.profile, name="profile"),

]
