# QL_BENHVIEN

Web quản lý bệnh viện có GIS (Django + PostGIS): tìm bệnh viện trên bản đồ, lọc gần nhất, đặt lịch khám, theo dõi lịch/phiếu khám, luồng bác sĩ.

## 1. Chức năng chính
- Người dùng:
  - Xem danh sách bệnh viện, lọc theo quận/loại hình/BHYT/cấp cứu/trạng thái mở.
  - Tìm bệnh viện gần nhất theo vị trí hiện tại.
  - Xem chi tiết bệnh viện, chỉ đường trên bản đồ.
  - Đặt lịch khám, xem lịch sắp tới, hủy lịch, xem lịch sử khám và phiếu khám.
- Bác sĩ:
  - Xem dashboard lịch khám theo trạng thái.
  - Bắt đầu khám, hoàn thành khám, tạo/sửa phiếu khám.
  - Xem thông báo và lịch sử bệnh nhân.
- Quản trị:
  - Có thể dùng Django Admin tại `/admin/`.
  - Trang quản trị giao diện mới vẫn dùng được tại `/quan-tri/`.
  - Nhập dữ liệu hàng loạt từ file Excel.

## 2. Yêu cầu môi trường
- Python 3.x
- PostgreSQL + PostGIS
- GDAL + GEOS (bắt buộc cho Django GIS)

## 3. Cấu hình `.env`
Tạo file `.env` ở thư mục gốc:

```env
DB_NAME=ql_benhvien
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
GDAL_PATH=C:\Users\ASUS\AppData\Local\Programs\OSGeo4W\bin\gdal312.dll
GEOS_PATH=C:\Users\ASUS\AppData\Local\Programs\OSGeo4W\bin\geos_c.dll
# Tuỳ chọn: bật tìm địa chỉ kiểu Google Maps trong form tạo bệnh viện
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## 4. Cài đặt dự án
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
venv\Scripts\python.exe -m pip install openpyxl
```

## 5. Khởi tạo database
```powershell
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
```

## 6. Dữ liệu mẫu (tùy chọn)
Xóa dữ liệu mẫu core:
```powershell
venv\Scripts\python.exe manage.py seed_core --purge-only
```

Tạo dữ liệu mẫu:
```powershell
venv\Scripts\python.exe manage.py seed_core --seed-only
```

Lưu ý:
- `--purge-only` **không xóa** `BenhNhan`.
- Lệnh chỉ xóa dữ liệu nghiệp vụ mẫu (lịch, phiếu, thông báo, bác sĩ, khoa, bệnh viện...).

## 7. Import dữ liệu từ Excel
File mẫu: `data.xlsx` (đặt ở thư mục gốc).

Import toàn bộ:
```powershell
venv\Scripts\python.exe manage.py import_hospitals data.xlsx
```

Import và cập nhật bản ghi đã có:
```powershell
venv\Scripts\python.exe manage.py import_hospitals data.xlsx --update-existing
```

Import từng sheet:
```powershell
venv\Scripts\python.exe manage.py import_hospitals data.xlsx --sheet Hospitals
```

### Cấu trúc các sheet
`Hospitals`:
`ten, dia_chi, quan, lat, lon, co_bhyt, co_cap_cuu, cap_cuu_24h, loai_hinh, gio_mo, gio_dong`

`Departments`:
`ten, benh_vien`

`Doctors`:
`ho_ten, so_dien_thoai, chuyen_khoa, khoa, benh_vien`

`DoctorSchedules`:
`bac_si, thu, gio_bat_dau, gio_ket_thuc, nghi`

Lưu ý import:
- Bắt buộc trong `Hospitals`: `ten`, `lat`, `lon`.
- Nếu `cap_cuu_24h=True`, hệ thống tự ép `co_cap_cuu=True`.
- Nếu một sheet phụ thiếu cột, lệnh sẽ cảnh báo và bỏ qua sheet đó, không dừng toàn bộ import.

## 8. Chạy dự án
```powershell
venv\Scripts\python.exe manage.py runserver
```

Truy cập:
- Web: `http://127.0.0.1:8000/`
- Django Admin: `http://127.0.0.1:8000/admin/`
- Quản trị giao diện mới: `http://127.0.0.1:8000/quan-tri/`

## 9. Tạo tài khoản admin (tùy chọn)
```powershell
venv\Scripts\python.exe manage.py createsuperuser
```

## 10. Kiểm tra nhanh trước khi demo/nộp
```powershell
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test
```

## 11. Bộ dữ liệu demo ổn định (thuyết trình)
Tạo nhanh bộ dữ liệu demo theo kịch bản:

```powershell
venv\Scripts\python.exe manage.py seed_demo --preset home
venv\Scripts\python.exe manage.py seed_demo --preset booking
venv\Scripts\python.exe manage.py seed_demo --preset doctor
```

Ý nghĩa preset:
- `home`: dữ liệu sạch để demo trang chủ/map/lọc.
- `booking`: có lịch chờ + lịch hủy để demo đặt/hủy/đặt lại.
- `doctor`: có lịch chờ/đang khám/đã xong và có phiếu khám mẫu.

Lưu ý:
- Mặc định `seed_demo` sẽ reset và seed lại dữ liệu trước khi áp preset.
- Dùng `--no-reset` nếu muốn giữ dữ liệu hiện tại:

```powershell
venv\Scripts\python.exe manage.py seed_demo --preset doctor --no-reset
```

Tài khoản demo sau khi chạy:
- Bệnh nhân: `0909000001 / 123456`
- Bác sĩ: `bsdemo / 123456`

## 12. Luồng demo đề xuất
1. Vào trang chủ, lọc bệnh viện theo quận + tìm nhanh theo tên.
2. Mở chi tiết bệnh viện, thử chỉ đường từ vị trí nhập tay.
3. Đăng nhập bệnh nhân, đặt lịch khám.
4. Vào “Lịch khám sắp tới”, hủy 1 lịch rồi đặt lại đúng khung giờ đó (được phép).
5. Đăng nhập bác sĩ, bắt đầu khám và tạo phiếu khám.
6. Quay lại tài khoản bệnh nhân, kiểm tra lịch sử khám + phiếu khám.
