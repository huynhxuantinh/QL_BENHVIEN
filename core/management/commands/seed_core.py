import datetime

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    BacSi,
    BaoHiemYTe,
    BenhNhan,
    BenhVien,
    GioLamViecBacSi,
    GioLamViecBenhVien,
    Khoa,
    LichKham,
    LichSuKhamBenh,
    LogHeThong,
    LogLichKham,
    PhieuKham,
    ThongBao,
)


class Command(BaseCommand):
    help = "Purge core data and seed sample dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge-only",
            action="store_true",
            help="Only delete core data, do not seed.",
        )
        parser.add_argument(
            "--seed-only",
            action="store_true",
            help="Only seed data, do not delete existing core data.",
        )

    def handle(self, *args, **options):
        purge_only = options.get("purge_only")
        seed_only = options.get("seed_only")

        if purge_only and seed_only:
            self.stdout.write(self.style.ERROR("Choose only one of --purge-only or --seed-only."))
            return

        if not seed_only:
            self._purge_core()
            if purge_only:
                return

        self._seed()
        self.stdout.write(self.style.SUCCESS("Seed completed."))

    def _purge_core(self):
        self.stdout.write("Deleting core data...")
        for model in [
            LogHeThong,
            LogLichKham,
            ThongBao,
            LichSuKhamBenh,
            PhieuKham,
            LichKham,
            GioLamViecBacSi,
            BacSi,
            GioLamViecBenhVien,
            Khoa,
            BenhNhan,
            BaoHiemYTe,
            BenhVien,
        ]:
            model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Core data deleted."))

    def _seed(self):
        self.stdout.write("Seeding sample data...")

        hospitals = [
            {
                "ten": "Benh vien Thong Nhat",
                "dia_chi": "95 Ly Thuong Kiet",
                "quan": "Tan Binh",
                "coords": (106.6536, 10.7873),
                "co_cap_cuu": True,
                "cap_cuu_24h": False,
                "co_bhyt": True,
                "gio_mo": datetime.time(6, 0),
                "gio_dong": datetime.time(18, 0),
                "loai_hinh": "cong",
            },
            {
                "ten": "Benh vien Cho Ray",
                "dia_chi": "201B Nguyen Chi Thanh",
                "quan": "Quan 5",
                "coords": (106.6581, 10.7531),
                "co_cap_cuu": True,
                "cap_cuu_24h": True,
                "co_bhyt": True,
                "gio_mo": datetime.time(6, 0),
                "gio_dong": datetime.time(18, 0),
                "loai_hinh": "cong",
            },
            {
                "ten": "Benh vien Dai hoc Y Duoc",
                "dia_chi": "215 Hong Bang",
                "quan": "Quan 5",
                "coords": (106.6542, 10.7555),
                "co_cap_cuu": False,
                "cap_cuu_24h": False,
                "co_bhyt": True,
                "gio_mo": datetime.time(7, 0),
                "gio_dong": datetime.time(17, 0),
                "loai_hinh": "cong",
            },
        ]

        department_names = ["Noi tong quat", "Ngoai tong quat", "Tim mach"]

        all_benh_vien = []
        all_khoa = []
        all_bac_si = []

        for data in hospitals:
            bv = BenhVien.objects.create(
                ten=data["ten"],
                dia_chi=data["dia_chi"],
                quan=data["quan"],
                vi_tri=Point(data["coords"][0], data["coords"][1], srid=4326),
                co_cap_cuu=data["co_cap_cuu"],
                cap_cuu_24h=data["cap_cuu_24h"],
                co_bhyt=data["co_bhyt"],
                gio_mo=data["gio_mo"],
                gio_dong=data["gio_dong"],
                loai_hinh=data["loai_hinh"],
            )
            all_benh_vien.append(bv)

            for thu in range(7):
                nghi = thu == 0
                GioLamViecBenhVien.objects.create(
                    benh_vien=bv,
                    thu=thu,
                    gio_mo=datetime.time(0, 0) if nghi else data["gio_mo"],
                    gio_dong=datetime.time(0, 0) if nghi else data["gio_dong"],
                    nghi=nghi,
                )

            for dept_name in department_names:
                all_khoa.append(Khoa.objects.create(ten=dept_name, benh_vien=bv))

        phone_base = 907000000
        for idx, khoa in enumerate(all_khoa, start=1):
            for n in range(2):
                phone = str(phone_base + idx * 10 + n)
                bac_si = BacSi.objects.create(
                    ho_ten=f"BS {khoa.ten} {n + 1}",
                    chuyen_khoa=khoa.ten,
                    khoa=khoa,
                    benh_vien=khoa.benh_vien,
                    so_dien_thoai=phone,
                )
                all_bac_si.append(bac_si)

                for thu in range(7):
                    nghi = thu == 0
                    GioLamViecBacSi.objects.create(
                        bac_si=bac_si,
                        thu=thu,
                        gio_bat_dau=datetime.time(0, 0) if nghi else datetime.time(8, 0),
                        gio_ket_thuc=datetime.time(0, 0) if nghi else datetime.time(17, 0),
                        nghi=nghi,
                    )

        today = timezone.localdate()
        patient_data = [
            ("Nguyen Van An", "0909000001", datetime.date(1995, 5, 12), "nam", "TP.HCM"),
            ("Tran Thi Bich", "0909000002", datetime.date(1998, 9, 3), "nu", "TP.HCM"),
            ("Le Hoang Long", "0909000003", datetime.date(1992, 2, 20), "nam", "TP.HCM"),
            ("Pham Minh Chau", "0909000004", datetime.date(1990, 12, 1), "nu", "TP.HCM"),
            ("Doan Quoc Huy", "0909000005", datetime.date(1988, 7, 8), "nam", "TP.HCM"),
        ]

        all_benh_nhan = []
        for i, (name, phone, birth, gender, address) in enumerate(patient_data, start=1):
            email = f"bn{i}@example.com"
            user = User.objects.filter(username=phone).first()
            if not user:
                user = User.objects.create_user(username=phone, password="123456", email=email)
            elif not user.email:
                user.email = email
                user.save()

            bhyt = None
            if i <= 3:
                bhyt = BaoHiemYTe.objects.create(
                    ma_bhyt=f"BHYT{i:04d}",
                    ngay_cap=today - datetime.timedelta(days=30),
                    ngay_het_han=today + datetime.timedelta(days=365),
                )

            benh_nhan = BenhNhan.objects.create(
                user=user,
                ho_ten=name,
                ngay_sinh=birth,
                gioi_tinh=gender,
                so_dien_thoai=phone,
                dia_chi=address,
                bhyt=bhyt,
            )
            all_benh_nhan.append(benh_nhan)

        appointment_date = today + datetime.timedelta(days=1)
        while (appointment_date.weekday() + 1) % 7 == 0:
            appointment_date += datetime.timedelta(days=1)

        sample_appointments = [
            (all_benh_nhan[0], all_bac_si[0], datetime.time(9, 0)),
            (all_benh_nhan[1], all_bac_si[0], datetime.time(9, 30)),
            (all_benh_nhan[2], all_bac_si[1], datetime.time(10, 0)),
        ]

        for benh_nhan, bac_si, gio in sample_appointments:
            lich = LichKham(
                benh_nhan=benh_nhan,
                bac_si=bac_si,
                ngay_kham=appointment_date,
                gio_kham=gio,
                ghi_chu="Kham tong quat",
            )
            lich.full_clean()
            lich.save()
