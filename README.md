
## QUY TRÌNH ĐÚNG MỖI KHI SỬA MODEL
python manage.py makemigrations
python manage.py migrate


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

# Setup
pip install python-dotenv
pip install django
1. Tạo file .env
2. Copy từ .env.example
3. Chạy migrate
4. Runserver

Kéo code mới nhất về
git pull

Code xong thì push lại

git add .
git commit -m "update"
git push
