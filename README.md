# QL_BENHVIEN

Ứng dụng web quản lý bệnh viện có GIS (Django + PostGIS):
- Tìm và lọc bệnh viện trên bản đồ.
- Đặt lịch khám, theo dõi lịch và phiếu khám.
- Luồng bác sĩ khám bệnh.
- Trang quản trị tùy biến tại `/quan-tri/`.

## 1) Tính năng chính

### Người dùng
- Xem danh sách bệnh viện, lọc theo phường/loại hình/BHYT/cấp cứu/trạng thái mở.
- Tìm bệnh viện gần vị trí hiện tại.
- Xem chi tiết bệnh viện và chỉ đường trên bản đồ.
- Gửi liên hệ/góp ý từ trang `/lien-he/` (email qua Mailtrap SMTP).
- Đặt lịch khám, xem lịch sắp tới, hủy lịch, xem lịch sử khám và phiếu khám.

### Bác sĩ
- Dashboard lịch khám theo trạng thái.
- Bắt đầu khám, hoàn thành khám, tạo/sửa phiếu khám.
- Xem thông báo và lịch sử bệnh nhân.

### Quản trị
- Admin giao diện riêng: `/quan-tri/`.
- Quản lý bệnh viện, khoa, bác sĩ, giờ làm việc, tài khoản user, lịch khám, phiếu khám...
- Import dữ liệu từ file Excel (`.xlsx`).

---

## 2) Yêu cầu môi trường

- Python 3.12+ (khuyến nghị dùng môi trường ảo).
- PostgreSQL + PostGIS.
- GDAL + GEOS (bắt buộc cho Django GIS).

---

## 3) Cấu hình `.env`

Tạo file `.env` ở thư mục gốc:

```env
DB_NAME=ql_benhvien
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

GDAL_PATH=C:\Users\ASUS\AppData\Local\Programs\OSGeo4W\bin\gdal312.dll
GEOS_PATH=C:\Users\ASUS\AppData\Local\Programs\OSGeo4W\bin\geos_c.dll

# Mailtrap SMTP (test email)
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=your_mailtrap_username
EMAIL_HOST_PASSWORD=your_mailtrap_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@qlbenhvien.local

```

---

## 4) Cài đặt dự án

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
venv\Scripts\python.exe -m pip install python-dotenv openpyxl
venv\Scripts\python.exe -m pip install openpyxl
```

---

## 5) Khởi tạo database

Chạy migrate:

```powershell
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
```

---

## 6) Chạy ứng dụng

```powershell
venv\Scripts\python.exe manage.py runserver
```

Truy cập:
- Web: `http://127.0.0.1:8000/`
- Admin giao diện riêng: `http://127.0.0.1:8000/quan-tri/`

---

## 7) Tạo tài khoản quản trị

```powershell
venv\Scripts\python.exe manage.py createsuperuser
```

Gửi mail test Mailtrap:
```powershell
venv\Scripts\python.exe manage.py send_test_email --to your_test@email.com
```

## 8) Seed dữ liệu mẫu

### Xóa dữ liệu nghiệp vụ mẫu
```powershell
venv\Scripts\python.exe manage.py seed_core --purge-only
```

### Tạo dữ liệu mẫu
```powershell
venv\Scripts\python.exe manage.py seed_core --seed-only
```

Ghi chú:
- `--purge-only` không xóa bảng bệnh nhân (`BenhNhan`) và user đăng nhập.
- Chỉ xóa dữ liệu nghiệp vụ như lịch khám, phiếu khám, thông báo, bác sĩ, khoa, bệnh viện...

---

## 9) Import dữ liệu từ Excel

### Import toàn bộ file
```powershell
venv\Scripts\python.exe manage.py import_hospitals data.xlsx
```

### Import và cập nhật bản ghi cũ theo `tên + địa chỉ`
```powershell
venv\Scripts\python.exe manage.py import_hospitals data.xlsx --update-existing
```

### Import theo từng sheet
```powershell
venv\Scripts\python.exe manage.py import_hospitals data.xlsx --sheet Hospitals
```

### Cấu trúc sheet

`Hospitals`:
- `ten, dia_chi, phuong, lat, lon, co_bhyt, co_cap_cuu, cap_cuu_24h, loai_hinh, gio_mo, gio_dong`

`Departments`:
- `ten, benh_vien`

`Doctors`:
- `ho_ten, so_dien_thoai, chuyen_khoa, khoa, benh_vien`

`DoctorSchedules`:
- `bac_si, thu, gio_bat_dau, gio_ket_thuc, nghi`

Lưu ý import:
- Bắt buộc trong `Hospitals`: `ten`, `lat`, `lon`.
- Nếu `cap_cuu_24h=True` thì `co_cap_cuu` phải `True` (hệ thống sẽ tự ép).
- Nếu sheet phụ thiếu cột bắt buộc, lệnh sẽ cảnh báo và bỏ qua sheet đó.

---

## 10) Dữ liệu demo ổn định (thuyết trình)

```powershell
venv\Scripts\python.exe manage.py seed_demo --preset home
venv\Scripts\python.exe manage.py seed_demo --preset booking
venv\Scripts\python.exe manage.py seed_demo --preset doctor
```

Ý nghĩa preset:
- `home`: dữ liệu sạch để demo trang chủ/map/lọc.
- `booking`: dữ liệu đặt/hủy/đặt lại lịch.
- `doctor`: dữ liệu đủ trạng thái khám + phiếu khám mẫu.

Không reset dữ liệu trước khi seed:

```powershell
venv\Scripts\python.exe manage.py seed_demo --preset doctor --no-reset
```

Tài khoản demo:
- Bệnh nhân: `0909000001 / 123456`
- Bác sĩ: `bsdemo / 123456`

---

## 11) Kiểm tra nhanh trước khi demo/nộp

```powershell
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test
```

---

## 12) Công nghệ & Tham khảo mở rộng

- CDN:
  - `cdnjs`: https://cdnjs.com/
  - `jsDelivr`: https://www.jsdelivr.com/
- Animation:
  - Anime.js: https://animejs.com/
  - AOS: https://michalsnik.github.io/aos/
- Pagination Django:
  - https://www.geeksforgeeks.org/python/use-pagination-with-django-class-based-generic-listview/
  - https://viblo.asia/p/pagination-in-django-PaLkDYwRvlX
- Mailtrap + Django SMTP:
  - https://mailtrap.io/blog/django-send-email/#Send-emails-in-Django-using-SMTP

Lưu ý triển khai trong project:
- Trang chủ dùng `AOS` + `anime.js` cho hiệu ứng nhẹ.
- Các tài nguyên map/JS/CSS bên thứ ba đã chuyển qua CDN `jsDelivr`/`cdnjs`.
- Phân trang vẫn dùng `Django Paginator` trong view để giữ tương thích logic hiện tại.

---

## 13) Luồng demo đề xuất

1. Vào trang chủ, lọc bệnh viện theo phường + tìm nhanh tên.
2. Mở chi tiết bệnh viện, thử chỉ đường từ vị trí nhập tay.
3. Đăng nhập bệnh nhân, đặt lịch khám.
4. Vào “Lịch khám sắp tới”, hủy 1 lịch rồi đặt lại.
5. Đăng nhập bác sĩ, bắt đầu khám và tạo phiếu khám.
6. Quay lại bệnh nhân, kiểm tra lịch sử khám + phiếu khám.
7. Đăng nhập admin vào `/quan-tri/`, xem dashboard và danh mục “Tài khoản”.

---
