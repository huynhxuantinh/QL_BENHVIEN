# Hướng dẫn cài đặt & chạy dự án QL_BENHVIEN

> Hướng dẫn này dành cho **máy Windows chưa cài bất kỳ thứ gì**.
> Đọc và làm đúng thứ tự từ trên xuống dưới.

---

## PHẦN A — CÀI PHẦN MỀM (Làm 1 lần, không cần lệnh)

### A1. Cài Python 3.12+

1. Truy cập: https://www.python.org/downloads/
2. Tải bản **Python 3.12.x** (Windows installer 64-bit).
3. Chạy file cài đặt.
4. ⚠️ **QUAN TRỌNG**: Tích chọn **"Add Python to PATH"** trước khi bấm Install.
5. Bấm **Install Now**.
6. Sau khi cài xong, mở PowerShell và kiểm tra:
   ```powershell
   python --version
   ```

   Kết quả mong đợi: `Python 3.12.x`

---

### A2. Cài PostgreSQL + PostGIS

#### Bước 1: Cài PostgreSQL

1. Truy cập: https://www.postgresql.org/download/windows/
2. Bấm **Download the installer** → Chọn phiên bản **16.x** (Windows x86-64).
3. Chạy file cài đặt, làm theo wizard:
   - **Password**: Đặt mật khẩu cho user `postgres` (nhớ lại để điền vào `.env`).
   - **Port**: Giữ nguyên `5432`.
   - Tích chọn tất cả components (PostgreSQL Server, pgAdmin, Stack Builder, Command Line Tools).
4. Sau khi cài xong, **Stack Builder** sẽ tự mở.

#### Bước 2: Cài PostGIS qua Stack Builder

1. Trong Stack Builder, chọn `PostgreSQL 16 on port 5432` → Next.
2. Mở rộng mục **Spatial Extensions** → Tích chọn **PostGIS 3.x**.
3. Next → tải và cài tự động.
4. Trong quá trình cài PostGIS, bấm **Yes** khi hỏi có tạo database mẫu không (hoặc bỏ qua, ta sẽ tạo tay ở bước sau).

> **Nếu Stack Builder không tự mở**: Tìm kiếm "Stack Builder" trong Start Menu.

#### Bước 3: Tạo database và bật PostGIS

1. Mở **pgAdmin 4** (tìm trong Start Menu).
2. Đăng nhập với mật khẩu `postgres` vừa tạo.
3. Chuột phải vào **Databases** → **Create** → **Database...** → Đặt tên `ql_benhvien` → Save.
4. Click vào database `ql_benhvien` → mở **Query Tool** (biểu tượng SQL).
5. Dán vào và chạy lệnh sau:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
6. Kết quả hiện `CREATE EXTENSION` là thành công.

---

### A3. Cài OSGeo4W (GDAL + GEOS — Bắt buộc cho bản đồ GIS)

1. Truy cập: https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe
2. Tải về và chạy `osgeo4w-setup.exe`.
3. Chọn **Express Install** → Next.
4. Trong danh sách packages, tìm và chọn:
   - `gdal`
   - `geos`
5. Cài đặt (tự tải và cài).
6. Sau khi cài xong, kiểm tra thư mục `C:\OSGeo4W\bin\`:
   - Tìm file có tên dạng `gdal3**.dll` (ví dụ: `gdal312.dll`, `gdal309.dll`).
   - Tìm file `geos_c.dll`.
7. **Ghi lại đúng tên file** để điền vào `.env` ở bước sau.

---

## PHẦN B — CÀI ĐẶT DỰ ÁN (Chạy lệnh)

> Mở **PowerShell** và điều hướng vào thư mục dự án trước khi chạy các lệnh dưới đây.
> Thư mục chứa `manage.py` là thư mục gốc đúng.

### B1. Tạo và kích hoạt môi trường ảo

```powershell
python -m venv venv
.\venv\Scripts\activate
```

> Sau khi kích hoạt thành công, dấu nhắc lệnh sẽ có `(venv)` ở đầu, ví dụ: `(venv) PS C:\...>`

---

### B2. Cài thư viện Python

```powershell
pip install -r requirements.txt
pip install python-dotenv openpyxl
```

**Danh sách thư viện đầy đủ:**

| Thư viện          | Phiên bản | Mục đích                                   |
| ------------------- | ----------- | --------------------------------------------- |
| `Django`          | 6.0.1       | Framework web chính                          |
| `asgiref`         | 3.11.0      | Hỗ trợ async cho Django                     |
| `psycopg2-binary` | 2.9.11      | Kết nối PostgreSQL                          |
| `Pillow`          | 11.3.0      | Xử lý upload ảnh bệnh viện, phiếu khám |
| `sqlparse`        | 0.5.5       | Phân tích SQL (dependency nội bộ Django)  |
| `tzdata`          | 2025.3      | Dữ liệu múi giờ `Asia/Ho_Chi_Minh`      |
| `python-dotenv`   | mới nhất  | Đọc cấu hình từ file `.env`            |
| `openpyxl`        | mới nhất  | Đọc file Excel `.xlsx` cho lệnh import   |

---

### B3. Tạo file `.env`

Tạo file tên `.env` tại **cùng thư mục với `manage.py`**, dán nội dung sau và điền đúng thông tin:

```env
# =============================
# DATABASE
# =============================
DB_NAME=ql_benhvien
DB_USER=postgres
DB_PASSWORD=MẬT_KHẨU_POSTGRES_CỦA_BẠN
DB_HOST=localhost
DB_PORT=5432

# =============================
# DJANGO
# =============================
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# =============================
# GIS — Điền đúng tên file DLL trong C:\OSGeo4W\bin\
# Ví dụ: gdal312.dll hoặc gdal309.dll tùy phiên bản
# =============================
GDAL_PATH=C:\OSGeo4W\bin\gdal312.dll
GEOS_PATH=C:\OSGeo4W\bin\geos_c.dll

# =============================
# EMAIL (Mailtrap để test gửi mail)
# Đăng ký miễn phí tại: https://mailtrap.io/
# =============================
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_HOST_USER=your_mailtrap_user
EMAIL_HOST_PASSWORD=your_mailtrap_password
EMAIL_PORT=2525
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@qlbenhvien.local
```

> ⚠️ **Lưu ý đường dẫn GDAL**: Kiểm tra trong `C:\OSGeo4W\bin\` xem file có tên `gdal312.dll` hay khác, rồi sửa lại cho đúng.

---

### B4. Migrate database

```powershell
python manage.py migrate
```

> Lệnh này tạo toàn bộ bảng trong database. Chạy lần đầu sẽ mất 10–30 giây.

---

### B5. Tạo tài khoản quản trị

```powershell
python manage.py createsuperuser
```

Nhập username, email, mật khẩu theo hướng dẫn hiện ra.

---

### B6. (Tùy chọn) Nhập dữ liệu

#### Import bệnh viện từ file Excel:

```powershell
python manage.py import_hospitals data.xlsx
```

#### Hoặc seed dữ liệu demo có sẵn:

```powershell
# Demo trang chủ + bản đồ
python manage.py seed_demo --preset home

# Demo đặt lịch
python manage.py seed_demo --preset booking

# Demo đầy đủ (bác sĩ + phiếu khám)
python manage.py seed_demo --preset doctor
```

**Tài khoản demo sau khi seed:**

- Bệnh nhân: `0909000001` / `123456`
- Bác sĩ: `bsdemo` / `123456`

---

### B7. Chạy server

```powershell
python manage.py runserver
```

Mở trình duyệt:

- **Trang chính**: http://127.0.0.1:8000/
- **Trang quản trị**: http://127.0.0.1:8000/quan-tri/

---

## PHẦN C — XỬ LÝ LỖI PHỔ BIẾN

### Lỗi 1: `GDAL_LIBRARY_PATH` not found

```
ImproperlyConfigured: Could not find the GDAL library
```

**Nguyên nhân**: Đường dẫn DLL trong `.env` sai.**Cách fix**:

1. Mở thư mục `C:\OSGeo4W\bin\`
2. Tìm file có tên `gdal*.dll` (ví dụ `gdal312.dll`)
3. Sửa lại `GDAL_PATH` trong `.env` cho khớp.

---

### Lỗi 2: Không kết nối được database

```
connection refused / password authentication failed
```

**Nguyên nhân**: PostgreSQL chưa chạy hoặc sai thông tin `.env`.**Cách fix**:

1. Mở **Services** (tìm trong Start Menu) → tìm `postgresql-x64-16` → bấm **Start**.
2. Kiểm tra lại `DB_PASSWORD` trong `.env` có đúng với mật khẩu đã đặt khi cài không.
3. Kiểm tra database `ql_benhvien` đã được tạo chưa (xem lại bước A2).

---

### Lỗi 3: `No module named 'dotenv'`

```
ModuleNotFoundError: No module named 'dotenv'
```

**Cách fix**:

```powershell
pip install python-dotenv
```

---

### Lỗi 4: `No module named 'openpyxl'`

```
Missing dependency openpyxl
```

**Cách fix**:

```powershell
pip install openpyxl
```

---

## PHẦN D — CHECKLIST TRƯỚC KHI CHẠY

- [ ] **Python 3.12+** đã cài và `python --version` chạy được
- [ ] **PostgreSQL** đang chạy (kiểm tra trong Services)
- [ ] Database `ql_benhvien` đã tạo trong pgAdmin
- [ ] Extension `postgis` đã được kích hoạt trong database
- [ ] **OSGeo4W** đã cài, có file `gdal*.dll` và `geos_c.dll` trong `C:\OSGeo4W\bin\`
- [ ] Môi trường ảo `venv` đã kích hoạt (có `(venv)` ở đầu dòng lệnh)
- [ ] Đã chạy `pip install -r requirements.txt` và `pip install python-dotenv openpyxl`
- [ ] File `.env` đã tạo với đúng thông tin (đặc biệt đường dẫn GDAL)
- [ ] Đã chạy `python manage.py migrate` thành công
- [ ] Server chạy được tại http://127.0.0.1:8000/

---

## PHẦN E — KHÔI PHỤC TỪ FILE BACKUP (Backup.sql)

> Dùng cách này **thay thế** cho bước B4 (migrate) + B6 (seed) nếu bạn đã có file backup sẵn.  
> File backup: `docx/Backup.sql`

### E1. Tạo database từ lệnh trong Backup.sql

File `Backup.sql` chứa lệnh tạo database:

```sql
CREATE DATABASE ql_benhvien001;
```

#### Cách 1: Chạy qua pgAdmin

1. Mở **pgAdmin 4** → đăng nhập.
2. Click chuột phải vào **Databases** → **Query Tool**.
3. Dán lệnh sau và nhấn **F5** (hoặc bấm nút Run):
   ```sql
   CREATE DATABASE ql_benhvien001;
   ```
4. Sau khi tạo xong, click vào database `ql_benhvien001` → mở **Query Tool** → bật PostGIS:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

#### Cách 2: Chạy qua PowerShell (psql)

```powershell
# Thay YOUR_PASSWORD bằng mật khẩu postgres của bạn
$env:PGPASSWORD = "YOUR_PASSWORD"
psql -U postgres -f "docx\Backup.sql"
```

---

### E2. Kích hoạt PostGIS cho database vừa tạo

```powershell
$env:PGPASSWORD = "YOUR_PASSWORD"
psql -U postgres -d ql_benhvien001 -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

---

### E3. Cập nhật file `.env`

Đảm bảo `DB_NAME` trong `.env` khớp với tên database vừa tạo:

```env
DB_NAME=ql_benhvien001
```

> ⚠️ Tên database trong file Backup.sql là `ql_benhvien001` (có hậu tố `001`), khác với tên mặc định `ql_benhvien` trong hướng dẫn B3.

---

### E4. Chạy migrate Django

Dù đã có database, vẫn cần chạy migrate để Django tạo các bảng nghiệp vụ:

```powershell
python manage.py migrate
```

---

### E5. (Tùy chọn) Tạo superuser và seed dữ liệu

```powershell
python manage.py createsuperuser
python manage.py seed_core
```

---

### Tóm tắt luồng dùng Backup.sql

```
[Backup.sql] → psql chạy → database ql_benhvien001 tạo xong
    → Bật PostGIS (CREATE EXTENSION postgis)
    → Cập nhật .env (DB_NAME=ql_benhvien001)
    → python manage.py migrate
    → python manage.py createsuperuser
    → python manage.py runserver
```
