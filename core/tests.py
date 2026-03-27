import datetime

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    BacSi,
    BenhNhan,
    BenhVien,
    GioLamViecBacSi,
    GioLamViecBenhVien,
    Khoa,
    LichKham,
    PhieuKham,
)


class DoctorFlowTests(TestCase):
    def setUp(self):
        self.hospital = BenhVien.objects.create(
            ten="Benh vien test",
            dia_chi="1 Duong Test",
            phuong="Quan 1",
            vi_tri=Point(106.7, 10.77, srid=4326),
            co_cap_cuu=True,
            cap_cuu_24h=False,
            co_bhyt=True,
            gio_mo=datetime.time(7, 0),
            gio_dong=datetime.time(17, 0),
            loai_hinh="cong",
        )
        self.department = Khoa.objects.create(
            ten="Noi tong quat",
            benh_vien=self.hospital,
        )

        self.doctor_user = User.objects.create_user(
            username="doctor1",
            password="pass12345",
        )
        self.other_doctor_user = User.objects.create_user(
            username="doctor2",
            password="pass12345",
        )
        self.patient_user = User.objects.create_user(
            username="0909000999",
            password="pass12345",
        )

        self.doctor = BacSi.objects.create(
            user=self.doctor_user,
            ho_ten="Bac si A",
            chuyen_khoa="Noi tong quat",
            khoa=self.department,
            benh_vien=self.hospital,
            so_dien_thoai="0909000001",
        )
        self.other_doctor = BacSi.objects.create(
            user=self.other_doctor_user,
            ho_ten="Bac si B",
            chuyen_khoa="Noi tong quat",
            khoa=self.department,
            benh_vien=self.hospital,
            so_dien_thoai="0909000002",
        )
        self.patient = BenhNhan.objects.create(
            user=self.patient_user,
            ho_ten="Benh nhan A",
            ngay_sinh=datetime.date(1995, 1, 1),
            gioi_tinh="nam",
            so_dien_thoai=self.patient_user.username,
            dia_chi="TP.HCM",
        )

        self.appointment = LichKham.objects.create(
            benh_nhan=self.patient,
            bac_si=self.doctor,
            ngay_kham=timezone.localdate() + datetime.timedelta(days=1),
            gio_kham=datetime.time(9, 0),
            trang_thai="cho",
            ghi_chu="",
        )

    def test_start_exam_requires_post(self):
        self.client.login(username="doctor1", password="pass12345")

        response = self.client.get(reverse("start_exam", args=[self.appointment.id]))

        self.assertRedirects(response, reverse("bac_si_home"))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.trang_thai, "cho")

    def test_start_exam_post_updates_status(self):
        self.client.login(username="doctor1", password="pass12345")

        response = self.client.post(reverse("start_exam", args=[self.appointment.id]))

        self.assertRedirects(response, reverse("bac_si_home"))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.trang_thai, "dang")

    def test_start_exam_permission_enforced(self):
        self.client.login(username="doctor2", password="pass12345")

        response = self.client.post(reverse("start_exam", args=[self.appointment.id]))

        self.assertEqual(response.status_code, 404)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.trang_thai, "cho")

    def test_start_exam_patient_is_redirected_home(self):
        self.client.login(username=self.patient_user.username, password="pass12345")

        response = self.client.post(reverse("start_exam", args=[self.appointment.id]))

        self.assertRedirects(response, reverse("home"))

    def test_doctor_exam_creates_phieu_and_marks_done(self):
        self.client.login(username="doctor1", password="pass12345")
        payload = {
            "trieu_chung": "Dau bung",
            "chan_doan": "Viem da day",
            "huong_dieu_tri": "Uong thuoc",
        }

        response = self.client.post(reverse("doctor_exam", args=[self.appointment.id]), payload)

        self.assertRedirects(response, reverse("bac_si_home"))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.trang_thai, "xong")

        phieu = PhieuKham.objects.get(lich_kham=self.appointment)
        self.assertEqual(phieu.benh_nhan, self.patient)
        self.assertEqual(phieu.chan_doan, "Viem da day")

    def test_doctor_exam_rejects_empty_payload(self):
        self.client.login(username="doctor1", password="pass12345")

        response = self.client.post(
            reverse("doctor_exam", args=[self.appointment.id]),
            {"trieu_chung": "", "chan_doan": "", "huong_dieu_tri": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(PhieuKham.objects.filter(lich_kham=self.appointment).exists())
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.trang_thai, "cho")

    def test_doctor_exam_permission_enforced(self):
        self.client.login(username="doctor2", password="pass12345")

        response = self.client.get(reverse("doctor_exam", args=[self.appointment.id]))

        self.assertEqual(response.status_code, 404)


class AppointmentBookingTests(TestCase):
    def setUp(self):
        self.hospital = BenhVien.objects.create(
            ten="Benh vien A",
            dia_chi="1 Duong A",
            phuong="Quan 1",
            vi_tri=Point(106.7, 10.77, srid=4326),
            co_cap_cuu=True,
            cap_cuu_24h=False,
            co_bhyt=True,
            gio_mo=datetime.time(7, 0),
            gio_dong=datetime.time(17, 0),
            loai_hinh="cong",
        )
        self.other_hospital = BenhVien.objects.create(
            ten="Benh vien B",
            dia_chi="2 Duong B",
            phuong="Quan 3",
            vi_tri=Point(106.68, 10.79, srid=4326),
            co_cap_cuu=True,
            cap_cuu_24h=False,
            co_bhyt=True,
            gio_mo=datetime.time(7, 0),
            gio_dong=datetime.time(17, 0),
            loai_hinh="cong",
        )
        self.department = Khoa.objects.create(ten="Noi", benh_vien=self.hospital)
        self.other_department = Khoa.objects.create(ten="Ngoai", benh_vien=self.other_hospital)

        self.doctor = BacSi.objects.create(
            ho_ten="Bac si A",
            chuyen_khoa="Noi",
            khoa=self.department,
            benh_vien=self.hospital,
            so_dien_thoai="0911000001",
        )
        self.other_doctor = BacSi.objects.create(
            ho_ten="Bac si B",
            chuyen_khoa="Ngoai",
            khoa=self.other_department,
            benh_vien=self.other_hospital,
            so_dien_thoai="0911000002",
        )

        # Thu 2 full-day working window so booking validation can pass.
        GioLamViecBacSi.objects.create(
            bac_si=self.doctor,
            thu=1,
            gio_bat_dau=datetime.time(7, 0),
            gio_ket_thuc=datetime.time(17, 0),
            nghi=False,
        )
        GioLamViecBenhVien.objects.create(
            benh_vien=self.hospital,
            thu=1,
            gio_mo=datetime.time(7, 0),
            gio_dong=datetime.time(17, 0),
            nghi=False,
        )

        self.user = User.objects.create_user(username="0911999999", password="pass12345")
        self.patient = BenhNhan.objects.create(
            user=self.user,
            ho_ten="Benh nhan test",
            ngay_sinh=datetime.date(1999, 1, 1),
            gioi_tinh="nam",
            so_dien_thoai=self.user.username,
            dia_chi="TP.HCM",
        )
        self.client.login(username=self.user.username, password="pass12345")

        # Find upcoming Monday for deterministic schedule validation.
        today = timezone.localdate()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        self.next_monday = today + datetime.timedelta(days=days_ahead)

    def test_booking_requires_department(self):
        response = self.client.post(
            reverse("dat_lich", args=[self.hospital.id]),
            {
                "bac_si": self.doctor.id,
                "ngay_kham": self.next_monday.isoformat(),
                "gio_kham": "09:00",
                "ghi_chu": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertFalse(LichKham.objects.filter(benh_nhan=self.patient).exists())

    def test_booking_rejects_doctor_outside_selected_hospital(self):
        response = self.client.post(
            reverse("dat_lich", args=[self.hospital.id]),
            {
                "khoa": str(self.department.id),
                "bac_si": self.other_doctor.id,
                "ngay_kham": self.next_monday.isoformat(),
                "gio_kham": "09:00",
                "ghi_chu": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("bac_si", response.context["form"].errors)
        self.assertFalse(LichKham.objects.filter(benh_nhan=self.patient).exists())

    def test_booking_success_redirects_to_upcoming_appointments(self):
        response = self.client.post(
            reverse("dat_lich", args=[self.hospital.id]),
            {
                "khoa": str(self.department.id),
                "bac_si": self.doctor.id,
                "ngay_kham": self.next_monday.isoformat(),
                "gio_kham": "09:00",
                "ghi_chu": "Tai kham",
            },
        )

        self.assertRedirects(response, reverse("upcoming_appointments"))
        self.assertTrue(
            LichKham.objects.filter(
                benh_nhan=self.patient,
                bac_si=self.doctor,
                ngay_kham=self.next_monday,
                gio_kham=datetime.time(9, 0),
            ).exists()
        )

    def test_booking_can_reuse_slot_when_previous_was_cancelled(self):
        LichKham.objects.create(
            benh_nhan=self.patient,
            bac_si=self.doctor,
            ngay_kham=self.next_monday,
            gio_kham=datetime.time(10, 0),
            trang_thai="huy",
            ghi_chu="Da huy",
        )

        response = self.client.post(
            reverse("dat_lich", args=[self.hospital.id]),
            {
                "khoa": str(self.department.id),
                "bac_si": self.doctor.id,
                "ngay_kham": self.next_monday.isoformat(),
                "gio_kham": "10:00",
                "ghi_chu": "Dat lai",
            },
        )

        self.assertRedirects(response, reverse("upcoming_appointments"))
        self.assertEqual(
            LichKham.objects.filter(
                benh_nhan=self.patient,
                bac_si=self.doctor,
                ngay_kham=self.next_monday,
                gio_kham=datetime.time(10, 0),
            ).count(),
            2,
        )


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin_demo",
            password="pass12345",
            email="admin@example.com",
        )
        self.normal_user = User.objects.create_user(
            username="user_demo",
            password="pass12345",
        )
        self.hospital = BenhVien.objects.create(
            ten="BV Admin Test",
            dia_chi="1 Duong Test",
            phuong="Quan 1",
            vi_tri=Point(106.7, 10.77, srid=4326),
            co_cap_cuu=True,
            cap_cuu_24h=False,
            co_bhyt=True,
            gio_mo=datetime.time(7, 0),
            gio_dong=datetime.time(17, 0),
            loai_hinh="cong",
        )
        self.department = Khoa.objects.create(
            ten="Khoa Admin Test",
            benh_vien=self.hospital,
        )
        self.doctor = BacSi.objects.create(
            ho_ten="Bac Si Admin Test",
            chuyen_khoa="Noi tong quat",
            khoa=self.department,
            benh_vien=self.hospital,
            so_dien_thoai="0909555666",
        )

    def test_admin_login_redirects_to_custom_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": "admin_demo", "password": "pass12345"},
        )
        self.assertRedirects(response, reverse("custom_admin_dashboard"))

    def test_custom_dashboard_requires_admin(self):
        self.client.login(username="user_demo", password="pass12345")
        response = self.client.get(reverse("custom_admin_dashboard"))
        self.assertRedirects(response, reverse("home"))

    def test_admin_can_open_custom_dashboard(self):
        self.client.login(username="admin_demo", password="pass12345")
        response = self.client.get(reverse("custom_admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_open_custom_management_pages(self):
        self.client.login(username="admin_demo", password="pass12345")
        self.assertEqual(self.client.get(reverse("custom_admin_hospitals")).status_code, 200)
        self.assertEqual(self.client.get(reverse("custom_admin_departments")).status_code, 200)
        self.assertEqual(self.client.get(reverse("custom_admin_doctors")).status_code, 200)
        self.assertEqual(self.client.get(reverse("custom_admin_model_list", args=["tai-khoan"])).status_code, 200)

    def test_admin_department_api_returns_departments_by_hospital(self):
        self.client.login(username="admin_demo", password="pass12345")
        response = self.client.get(
            reverse("custom_admin_departments_api"),
            {"benh_vien_id": self.hospital.id},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["id"], self.department.id)

    def test_non_admin_cannot_use_department_api(self):
        self.client.login(username="user_demo", password="pass12345")
        response = self.client.get(
            reverse("custom_admin_departments_api"),
            {"benh_vien_id": self.hospital.id},
        )
        self.assertEqual(response.status_code, 403)

    def test_doctor_schedule_form_shows_hospital_in_doctor_option(self):
        self.client.login(username="admin_demo", password="pass12345")
        response = self.client.get(reverse("custom_admin_model_create", args=["gio-lam-viec-bac-si"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bac Si Admin Test - BV Admin Test")

    def test_admin_can_create_user_from_custom_admin(self):
        self.client.login(username="admin_demo", password="pass12345")
        response = self.client.post(
            reverse("custom_admin_model_create", args=["tai-khoan"]),
            {
                "username": "staff_from_custom",
                "email": "staff@example.com",
                "first_name": "Staff",
                "last_name": "Custom",
                "is_active": "on",
                "is_staff": "on",
                "is_superuser": "",
                "password": "Staff@123456",
            },
        )
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="staff_from_custom")
        self.assertTrue(created_user.check_password("Staff@123456"))
        self.assertTrue(created_user.is_staff)

    def test_admin_edit_own_password_keeps_session(self):
        self.client.login(username="admin_demo", password="pass12345")
        response = self.client.post(
            reverse("custom_admin_model_edit", args=["tai-khoan", self.admin_user.id]),
            {
                "username": "admin_demo",
                "email": "admin@example.com",
                "first_name": "",
                "last_name": "",
                "is_active": "on",
                "is_staff": "on",
                "is_superuser": "on",
                "password": "NewPass@12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        # Still authenticated after changing own password.
        follow = self.client.get(reverse("custom_admin_model_list", args=["tai-khoan"]))
        self.assertEqual(follow.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password("NewPass@12345"))

    def test_django_admin_url_enabled(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
