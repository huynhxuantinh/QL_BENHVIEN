import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import BenhVien, BenhVienHinhAnh


class Command(BaseCommand):
    help = 'Import hình ảnh bệnh viện từ thư mục media vào database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Xem trước mà không import',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = Path('media') / 'benh_vien'
        
        if not media_root.exists():
            self.stdout.write(self.style.ERROR(f'Không tìm thấy thư mục {media_root}'))
            return

        imported_count = 0
        failed_count = 0

        # Quét từng thư mục bệnh viện
        for hospital_folder in sorted(media_root.iterdir()):
            if not hospital_folder.is_dir():
                continue

            try:
                hospital_id = int(hospital_folder.name)
            except ValueError:
                self.stdout.write(self.style.WARNING(f'Bỏ qua folder: {hospital_folder.name} (không phải ID)'))
                continue

            # Kiểm tra bệnh viện tồn tại
            try:
                hospital = BenhVien.objects.get(id=hospital_id)
            except BenhVien.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Bệnh viện ID {hospital_id} không tồn tại'))
                continue

            # Quét các file ảnh trong thư mục
            image_files = sorted([
                f for f in hospital_folder.iterdir() 
                if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
            ])

            if not image_files:
                self.stdout.write(f'Bệnh viện {hospital.ten}: Không có file ảnh')
                continue

            for idx, image_path in enumerate(image_files):
                # Kiểm tra ảnh đã tồn tại trong DB chưa
                relative_path = f'benh_vien/{hospital_id}/{image_path.name}'
                exists = BenhVienHinhAnh.objects.filter(
                    benh_vien=hospital,
                    hinh_anh=relative_path
                ).exists()

                if exists:
                    self.stdout.write(f'  ✓ Đã import: {image_path.name}')
                    continue

                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] Sẽ import: {image_path.name}')
                    imported_count += 1
                    continue

                try:
                    # Đọc file ảnh
                    with open(image_path, 'rb') as f:
                        file_content = ContentFile(f.read(), name=image_path.name)

                        # Tạo bản ghi BenhVienHinhAnh
                        # Lưu ý: hinh_anh field sẽ tự động tính upload_to path
                        BenhVienHinhAnh.objects.create(
                            benh_vien=hospital,
                            hinh_anh=file_content,
                            mo_ta='',
                            thu_tu=idx,
                            la_anh_dai_dien=(idx == 0),  # Ảnh đầu tiên là ảnh đại diện
                        )
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Import: {image_path.name}'))
                    imported_count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Lỗi {image_path.name}: {str(e)}'))
                    failed_count += 1

            self.stdout.write(f'{hospital.ten}: {len(image_files)} file')

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Hoàn thành ===\n'
            f'Import thành công: {imported_count}\n'
            f'Lỗi: {failed_count}\n'
        ))
