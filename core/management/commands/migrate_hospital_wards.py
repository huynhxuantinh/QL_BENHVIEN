from django.core.management.base import BaseCommand
from core.models import BenhVien, GisWard, Ward, BenhNhan
from django.db import transaction

class Command(BaseCommand):
    help = 'Map BenhVien to Ward using GisWard geometries'

    def handle(self, *args, **kwargs):
        self.stdout.write("Mapping BenhVien...")
        benhvien_list = BenhVien.objects.all()
        mapped_bv = 0
        with transaction.atomic():
            for bv in benhvien_list:
                if not bv.vi_tri:
                    continue
                gis_ward = GisWard.objects.filter(geom__contains=bv.vi_tri).first()
                if gis_ward:
                    bv.phuong_xa_fk = gis_ward.ward_code
                    bv.save(update_fields=['phuong_xa_fk'])
                    mapped_bv += 1
                else:
                    self.stdout.write(self.style.WARNING(f"BenhVien ID {bv.id} point outside all wards!"))

        self.stdout.write(self.style.SUCCESS(f"Successfully mapped {mapped_bv}/{benhvien_list.count()} BenhVien."))
