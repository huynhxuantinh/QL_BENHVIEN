# Hệ thống quản lý bệnh viện + GIS

Ứng dụng quản lý bệnh viện, lịch khám và bản đồ GIS (PostGIS + GeoDjango).

## Tính năng chính
- Tra cứu bệnh viện, hiển thị bản đồ và khoảng cách.
- Lọc theo bán kính, loại hình (công/tư/quốc tế), BHYT, cấp cứu, đang mở.
- Đặt lịch khám, xem lịch sắp tới, lịch sử khám.
- Thông báo nhắc lịch.
- Trang bác sĩ: danh sách lịch, khám bệnh, tạo phiếu khám.

## Yêu cầu môi trường
- Python >= 3.10
- PostgreSQL + PostGIS
- GDAL, GEOS
- Windows: khuyến nghị OSGeo4W

## Cài đặt

### 1. Tạo môi trường ảo
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Cài thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình database
Tạo database PostgreSQL: `ql_benhvien` và bật PostGIS.

Thiết lập biến môi trường (Windows ví dụ):
```
GDAL_PATH=C:\OSGeo4W\bin\gdal312.dll
GEOS_PATH=C:\OSGeo4W\bin\geos_c.dll
```

### 4. Migrate
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Tạo tài khoản admin
```bash
python manage.py createsuperuser
```

### 6. Chạy server
```bash
python manage.py runserver
```

Truy cập:
- Trang admin: `http://127.0.0.1:8000/admin`
- Trang web: `http://127.0.0.1:8000/`

## Seed dữ liệu mẫu (nếu có)
```bash
venv\Scripts\python.exe manage.py seed_core --purge-only
venv\Scripts\python.exe manage.py seed_core --seed-only
```

## Ghi chú
- Khi sửa `models.py`, nhớ chạy lại:
```bash
python manage.py makemigrations
python manage.py migrate
```
- Cache đang dùng `LocMemCache` (phù hợp dev).

## Làm việc với Git
```bash
git pull
git add .
git commit -m "update"
git push
```
