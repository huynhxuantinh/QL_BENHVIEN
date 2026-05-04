from django.urls import path
from . import views

urlpatterns = [

    # Trang chủ
    path("", views.home, name="home"),
    path("gioi-thieu/", views.gioi_thieu, name="gioi_thieu"),

    # Chi tiết bệnh viện
    path("benh-vien/<int:id>/", views.hospital_detail, name="hospital_detail"),

    # Đặt lịch theo bệnh viện
    path("dat-lich/<int:bv_id>/", views.dat_lich, name="dat_lich"),

    # Auth
    path("login/", views.user_login, name="login"),
    path("quan-tri/", views.custom_admin_dashboard, name="custom_admin_dashboard"),
    path("quan-tri/benh-vien/", views.custom_admin_hospitals, name="custom_admin_hospitals"),
    path("quan-tri/benh-vien/tao/", views.custom_admin_hospital_create, name="custom_admin_hospital_create"),
    path("quan-tri/benh-vien/<int:pk>/sua/", views.custom_admin_hospital_edit, name="custom_admin_hospital_edit"),
    path("quan-tri/benh-vien/<int:pk>/xoa/", views.custom_admin_hospital_delete, name="custom_admin_hospital_delete"),
    path("quan-tri/khoa/", views.custom_admin_departments, name="custom_admin_departments"),
    path("quan-tri/khoa/tao/", views.custom_admin_department_create, name="custom_admin_department_create"),
    path("quan-tri/khoa/<int:pk>/sua/", views.custom_admin_department_edit, name="custom_admin_department_edit"),
    path("quan-tri/khoa/<int:pk>/xoa/", views.custom_admin_department_delete, name="custom_admin_department_delete"),
    path("quan-tri/bac-si/", views.custom_admin_doctors, name="custom_admin_doctors"),
    path("quan-tri/bac-si/tao/", views.custom_admin_doctor_create, name="custom_admin_doctor_create"),
    path("quan-tri/bac-si/<int:pk>/sua/", views.custom_admin_doctor_edit, name="custom_admin_doctor_edit"),
    path("quan-tri/bac-si/<int:pk>/xoa/", views.custom_admin_doctor_delete, name="custom_admin_doctor_delete"),
    path("quan-tri/gioi-thieu/", views.custom_admin_about_content, name="custom_admin_about_content"),
    path("quan-tri/api/khoa/", views.custom_admin_departments_api, name="custom_admin_departments_api"),
    path("quan-tri/du-lieu/<slug:model_key>/", views.custom_admin_model_list, name="custom_admin_model_list"),
    path("quan-tri/du-lieu/<slug:model_key>/tao/", views.custom_admin_model_create, name="custom_admin_model_create"),
    path("quan-tri/du-lieu/<slug:model_key>/<int:pk>/sua/", views.custom_admin_model_edit, name="custom_admin_model_edit"),
    path("quan-tri/du-lieu/<slug:model_key>/<int:pk>/xoa/", views.custom_admin_model_delete, name="custom_admin_model_delete"),
    path("register/", views.register, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path("quen-mat-khau/", views.forgot_password, name="forgot_password"),
    path("lien-he/", views.contact_feedback, name="contact_feedback"),
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
