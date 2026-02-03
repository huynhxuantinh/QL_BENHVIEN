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
    path("bac-si/benh-nhan/<int:benh_nhan_id>/", views.bac_si_patient_detail, name="bac_si_patient_detail"),
    path("bac-si/lich/<int:lich_id>/bat-dau/", views.start_exam, name="start_exam"),
    path("bac-si/thong-bao/", views.bac_si_notifications, name="bac_si_notifications"),
    path("bac-si/lich-lam-viec/", views.bac_si_schedule, name="bac_si_schedule"),
    path("bac-si/phieu-kham/<int:phieu_id>/sua/", views.bac_si_phieu_kham_edit, name="bac_si_phieu_kham_edit"),
    path("profile/", views.profile, name="profile"),

]
