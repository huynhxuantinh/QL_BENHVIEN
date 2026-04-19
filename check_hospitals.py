#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital.settings')
django.setup()

from core.models import BenhVien

hospitals = list(BenhVien.objects.all().order_by('id').values('id', 'ten'))
print(f'Tổng bệnh viện: {len(hospitals)}')
print('\nDanh sách bệnh viện:')
for h in hospitals:
    print(f'  {h["id"]}: {h["ten"]}')
