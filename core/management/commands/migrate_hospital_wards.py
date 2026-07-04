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

        self.stdout.write("Mapping BenhNhan (Text-based naive match)...")
        benhnhan_list = BenhNhan.objects.all()
        mapped_bn = 0
        # Load all wards into memory to avoid N+1 queries for string matching
        all_wards = list(Ward.objects.select_related('district_code', 'district_code__province_code').all())
        
        with transaction.atomic():
            for bn in benhnhan_list:
                if not bn.dia_chi:
                    continue
                dia_chi_lower = bn.dia_chi.lower()
                # Sort wards by length descending to match longer specific names first (e.g. "Phường 10" vs "Phường 1")
                for w in sorted(all_wards, key=lambda x: len(x.name), reverse=True):
                    if w.name.lower() in dia_chi_lower and w.district_code.province_code.name.lower() in dia_chi_lower:
                        bn.phuong_xa_fk = w
                        bn.save(update_fields=['phuong_xa_fk'])
                        mapped_bn += 1
                        break
        
        self.stdout.write(self.style.SUCCESS(f"Successfully mapped {mapped_bn}/{benhnhan_list.count()} BenhNhan."))
