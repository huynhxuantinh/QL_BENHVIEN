# Hệ thống quản lý bệnh viện + GIS

## 1. Yêu cầu môi trường
- Python >= 3.10
- PostgreSQL + PostGIS
- GDAL
- OSGeo4W (Windows)

## 2. Cài đặt

### Clone project
git clone <link github>
cd QL_BENHVIEN

### Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate

### Cài thư viện
pip install -r requirements.txt

### Cấu hình database
Tạo database: ql_benhvien (PostgreSQL + PostGIS)

Chỉnh file: hospital/settings.py

### Migrate
python manage.py makemigrations
python manage.py migrate

### Tạo admin
python manage.py createsuperuser

### Chạy server
python manage.py runserver

Truy cập:
http://127.0.0.1:8000/admin
