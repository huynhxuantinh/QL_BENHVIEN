from django.shortcuts import render, get_object_or_404, redirect
import datetime
import math
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from .models import BaoHiemYTe

from .models import (
    BenhVien,
    BenhNhan,
    BacSi,
    GioLamViecBenhVien,
    LichKham,
    LichSuKhamBenh,
    PhieuKham,
    ThongBao,
)

from .forms import DatLichForm


# ==========================
# TRANG CHỦ
# ==========================
def home(request):

    bvs = BenhVien.objects.all().prefetch_related("gio_lam_viecs")
    unread_count = 0
    display_name = None
    user_lat = None
    user_lon = None
    radius_km = None
    filter_open = request.GET.get("open") == "1"
    filter_emergency = request.GET.get("emergency") == "1"

    lat_str = request.GET.get("lat")
    lon_str = request.GET.get("lon")
    radius_str = request.GET.get("radius")

    user_point = None
    if lat_str and lon_str:
        try:
            user_lat = float(lat_str)
            user_lon = float(lon_str)
            if -90 <= user_lat <= 90 and -180 <= user_lon <= 180:
                user_point = Point(user_lon, user_lat, srid=4326)
        except ValueError:
            user_point = None

    if radius_str:
        try:
            radius_km = float(radius_str)
            if radius_km <= 0:
                radius_km = None
        except ValueError:
            radius_km = None

    if user_point:
        bvs = bvs.annotate(distance=Distance("vi_tri", user_point))
        if radius_km:
            bvs = bvs.filter(vi_tri__distance_lte=(user_point, D(km=radius_km)))
        bvs = bvs.order_by("distance")
    if request.user.is_authenticated:
        unread_count = ThongBao.objects.filter(
            nguoi_nhan=request.user,
            da_doc=False,
        ).count()
        benh_nhan = BenhNhan.objects.filter(
            so_dien_thoai=request.user.username
        ).only("ho_ten").first()
        display_name = benh_nhan.ho_ten if benh_nhan else request.user.username

    def point_to_latlon(point):
        if not point:
            return None, None
        x = point.x
        y = point.y
        is_web_mercator = point.srid == 3857 or abs(x) > 180 or abs(y) > 90
        if is_web_mercator:
            max_merc = 20037508.34
            world_width = max_merc * 2
            if x > max_merc or x < -max_merc:
                x = ((x + max_merc) % world_width) - max_merc
            if y > max_merc:
                y = max_merc
            elif y < -max_merc:
                y = -max_merc
            lon = x * 180.0 / 20037508.34
            lat = y * 180.0 / 20037508.34
            lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2)
            if abs(lat) <= 90 and abs(lon) <= 180:
                return lat, lon
            return None, None
        return y, x

    now = timezone.localtime()
    thu = (now.weekday() + 1) % 7
    computed_bvs = []
    for bv in bvs:
        gio_lam = None
        for glv in bv.gio_lam_viecs.all():
            if glv.thu == thu:
                gio_lam = glv
                break

        if gio_lam:
            if gio_lam.nghi:
                is_open = False
            else:
                is_open = gio_lam.gio_mo <= now.time() <= gio_lam.gio_dong
        else:
            is_open = bv.gio_mo <= now.time() <= bv.gio_dong

        emergency_active = bv.cap_cuu_24h or (bv.co_cap_cuu and is_open)

        map_lat, map_lon = point_to_latlon(bv.vi_tri) if bv.vi_tri else (None, None)
        setattr(bv, "map_lat", map_lat)
        setattr(bv, "map_lon", map_lon)
        setattr(bv, "is_open", is_open)
        setattr(bv, "emergency_active", emergency_active)

        distance_km = None
        if hasattr(bv, "distance") and bv.distance is not None:
            if hasattr(bv.distance, "km"):
                distance_km = round(bv.distance.km, 2)
            else:
                distance_km = round(bv.distance * 111.139, 2)
        setattr(bv, "distance_km", distance_km)
        if filter_open and not bv.is_open:
            continue
        if filter_emergency and not bv.emergency_active:
            continue
        computed_bvs.append(bv)

    bvs = computed_bvs

    map_data = []
    for bv in bvs:
        if bv.map_lat is None or bv.map_lon is None:
            continue
        map_data.append({
            "id": bv.id,
            "name": bv.ten,
            "lat": bv.map_lat,
            "lon": bv.map_lon,
            "open": bv.is_open,
            "emergency": bv.emergency_active,
            "distance_km": bv.distance_km,
        })

    return render(request, "core/home.html", {
        "bvs": bvs,
        "unread_count": unread_count,
        "display_name": display_name,
        "user_lat": user_lat,
        "user_lon": user_lon,
        "radius_km": radius_km,
        "filter_open": filter_open,
        "filter_emergency": filter_emergency,
        "map_data": map_data,
    })


# ==========================
# CHI TIẾT BỆNH VIỆN
# ==========================
def hospital_detail(request, id):

    bv = get_object_or_404(BenhVien, id=id)

    khoas = bv.khoas.all()
    bac_sis = bv.bac_sis.all()
    gio_lam_viec = GioLamViecBenhVien.objects.filter(benh_vien=bv).order_by("thu")
    map_lat = None
    map_lon = None
    if bv.vi_tri:
        x = bv.vi_tri.x
        y = bv.vi_tri.y

        is_web_mercator = bv.vi_tri.srid == 3857 or abs(x) > 180 or abs(y) > 90
        if is_web_mercator:
            max_merc = 20037508.34
            world_width = max_merc * 2
            if x > max_merc or x < -max_merc:
                x = ((x + max_merc) % world_width) - max_merc
            if y > max_merc:
                y = max_merc
            elif y < -max_merc:
                y = -max_merc
            lon = x * 180.0 / 20037508.34
            lat = y * 180.0 / 20037508.34
            lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2)
            map_lat, map_lon = lat, lon
        else:
            map_lat, map_lon = y, x

        if map_lat is not None and map_lon is not None:
            if abs(map_lat) > 90 or abs(map_lon) > 180:
                map_lat = None
                map_lon = None

    return render(request, "core/hospital_detail.html", {
        "bv": bv,
        "khoas": khoas,
        "bac_sis": bac_sis,
        "gio_lam_viec": gio_lam_viec,
        "map_lat": map_lat,
        "map_lon": map_lon,
    })


# ==========================
# ĐẶT LỊCH KHÁM (BỆNH NHÂN)
# ==========================
@login_required
def dat_lich(request, bv_id):

    benh_vien = get_object_or_404(BenhVien, id=bv_id)

    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Bạn chưa có hồ sơ bệnh nhân"
        })

    khoas = benh_vien.khoas.all()

    khoa_id = request.GET.get("khoa")

    bac_sis = None
    bac_si_schedules = None

    if khoa_id:
        bac_sis = benh_vien.bac_sis.filter(khoa_id=khoa_id).prefetch_related("gio_lam_viecs")
        bac_si_schedules = []
        for bs in bac_sis:
            bac_si_schedules.append({
                "bac_si": bs,
                "gio_lam_viecs": bs.gio_lam_viecs.all().order_by("thu"),
            })

    if request.method == "POST":

        form = DatLichForm(request.POST)

        if khoa_id:
            form.fields["bac_si"].queryset = bac_sis

        if form.is_valid():

            lich = form.save(commit=False)
            lich.benh_nhan = benh_nhan
            try:
                lich.full_clean()
                lich.save()
            except ValidationError as exc:
                for field, errors in exc.message_dict.items():
                    if field in form.fields:
                        for error in errors:
                            form.add_error(field, error)
                    else:
                        for error in errors:
                            form.add_error(None, error)
                messages.error(request, "Không thể đặt lịch. Vui lòng kiểm tra lại thông tin.")
                return render(request, "core/appointment.html", {
                    "form": form,
                    "benh_vien": benh_vien,
                    "benh_nhan": benh_nhan,
                    "khoas": khoas,
                    "bac_sis": bac_sis,
                    "bac_si_schedules": bac_si_schedules,
                    "khoa_id": khoa_id
                })
            except IntegrityError:
                form.add_error("ngay_kham", "Bạn đã có lịch khám trong ngày này.")
                messages.error(request, "Không thể đặt lịch. Vui lòng kiểm tra lại thông tin.")
                return render(request, "core/appointment.html", {
                    "form": form,
                    "benh_vien": benh_vien,
                    "benh_nhan": benh_nhan,
                    "khoas": khoas,
                    "bac_sis": bac_sis,
                    "bac_si_schedules": bac_si_schedules,
                    "khoa_id": khoa_id
                })

            messages.success(request, "Đặt lịch thành công")

            ThongBao.objects.create(
                nguoi_nhan=request.user,
                loai="lich_kham",
                tieu_de="Đặt lịch thành công",
                noi_dung=(
                    f"Tạo lịch khám vào ngày {lich.ngay_kham} lúc {lich.gio_kham} với bác sĩ {lich.bac_si.ho_ten}."
                ),
                lien_ket="/lich-kham-sap-toi/",
            )
            return redirect("home")
        else:
            messages.error(request, "Không thể đặt lịch. Vui lòng kiểm tra lại thông tin.")

    else:

        form = DatLichForm()

        if khoa_id:
            form.fields["bac_si"].queryset = bac_sis
        else:
            form.fields["bac_si"].queryset = BacSi.objects.none()

    return render(request, "core/appointment.html", {
        "form": form,
        "benh_vien": benh_vien,
        "benh_nhan": benh_nhan,
        "khoas": khoas,
        "bac_sis": bac_sis,
        "bac_si_schedules": bac_si_schedules,
        "khoa_id": khoa_id
    })


# ==========================
# LỊCH KHÁM SẮP TỚI (BỆNH NHÂN)
# ==========================
@login_required
def upcoming_appointments(request):
    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Bạn chưa có hồ sơ bệnh nhân"
        })

    today = timezone.localdate()
    all_upcoming = LichKham.objects.filter(
        benh_nhan=benh_nhan,
        ngay_kham__gte=today,
    ).order_by("ngay_kham", "gio_kham")

    lich_khams = all_upcoming.exclude(trang_thai="huy").exclude(trang_thai="xong")
    lich_huy = all_upcoming.filter(trang_thai="huy")

    now = timezone.localtime()
    window_end = now + datetime.timedelta(hours=24)
    tz = timezone.get_current_timezone()
    for lich in lich_khams.filter(trang_thai="cho"):
        lich_dt = datetime.datetime.combine(lich.ngay_kham, lich.gio_kham)
        lich_dt = timezone.make_aware(lich_dt, tz)
        if now <= lich_dt <= window_end:
            ThongBao.objects.get_or_create(
                nguoi_nhan=request.user,
                loai="nhac_nho",
                lien_ket=f"/lich-kham-sap-toi/?lich={lich.id}",
                defaults={
                    "tieu_de": "Nhắc lịch khám",
                    "noi_dung": (
                        f"Bạn có lịch khám vào ngày {lich.ngay_kham} lúc {lich.gio_kham} với bác sĩ {lich.bac_si.ho_ten}."
                    ),
                },
            )

    return render(request, "core/upcoming_appointments.html", {
        "benh_nhan": benh_nhan,
        "lich_khams": lich_khams,
        "lich_huy": lich_huy,
    })


# ==========================
# HỦY LỊCH KHÁM (BỆNH NHÂN)
# ==========================
@login_required
def cancel_appointment(request, lich_id):
    if request.method != "POST":
        return redirect("upcoming_appointments")

    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Bạn chưa có hồ sơ bệnh nhân"
        })

    lich = get_object_or_404(LichKham, id=lich_id, benh_nhan=benh_nhan)

    if lich.trang_thai == "huy":
        messages.error(request, "Lịch khám đã bị hủy trước đó.")
        return redirect("upcoming_appointments")

    if lich.trang_thai in ("dang", "xong"):
        messages.error(request, "Không thể hủy lịch đang khám hoặc đã hoàn thành.")
        return redirect("upcoming_appointments")

    now = timezone.localtime()
    if lich.ngay_kham < now.date() or (
        lich.ngay_kham == now.date() and lich.gio_kham <= now.time()
    ):
        messages.error(request, "Không thể hủy lịch đã đến giờ khám.")
        return redirect("upcoming_appointments")

    lich.trang_thai = "huy"
    lich.save()
    ThongBao.objects.create(
        nguoi_nhan=request.user,
        loai="he_thong",
        tieu_de="Đã hủy lịch khám",
        noi_dung=(
            f"Hủy lịch khám vào ngày {lich.ngay_kham} lúc {lich.gio_kham} với bác sĩ {lich.bac_si.ho_ten}."
        ),
        lien_ket="/lich-kham-sap-toi/",
    )

    messages.success(request, "Đã hủy lịch khám thành công.")
    return redirect("upcoming_appointments")

# ==========================
# LỊCH SỬ KHÁM (BỆNH NHÂN)
# ==========================
@login_required
def medical_history(request):
    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Bạn chưa có hồ sơ bệnh nhân"
        })

    lich_su = (
        LichSuKhamBenh.objects.filter(benh_nhan=benh_nhan)
        .select_related("bac_si", "benh_vien", "phieu_kham")
        .order_by("-ngay_kham", "-ngay_tao")
    )

    return render(request, "core/medical_history.html", {
        "benh_nhan": benh_nhan,
        "lich_su": lich_su,
    })


# ==========================
# CHI TIẾT PHIẾU KHÁM
# ==========================
@login_required
def phieu_kham_detail(request, phieu_id):
    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Bạn chưa có hồ sơ bệnh nhân"
        })

    phieu = get_object_or_404(PhieuKham, id=phieu_id, benh_nhan=benh_nhan)

    return render(request, "core/phieu_kham_detail.html", {
        "benh_nhan": benh_nhan,
        "phieu": phieu,
    })


# ==========================
# DASHBOARD BÁC SĨ
# ==========================
@login_required
def doctor_dashboard(request):

    try:
        bac_si = request.user.bac_si
    except:
        return redirect("home")


    lich_khams = LichKham.objects.filter(
        bac_si=bac_si
    ).order_by("ngay_kham", "gio_kham")


    return render(request, "core/doctor_dashboard.html", {
        "bac_si": bac_si,
        "lich_khams": lich_khams
    })


# ==========================
# KHÁM BỆNH (TẠO PHIẾU)
# ==========================
@login_required
def doctor_exam(request, lich_id):

    try:
        bac_si = request.user.bac_si
    except:
        return redirect("home")


    lich = get_object_or_404(
        LichKham,
        id=lich_id,
        bac_si=bac_si
    )


    if request.method == "POST":

        trieu_chung = request.POST["trieu_chung"]
        chan_doan = request.POST["chan_doan"]
        huong_dieu_tri = request.POST["huong_dieu_tri"]


        PhieuKham.objects.create(
            benh_nhan=lich.benh_nhan,
            lich_kham=lich,
            trieu_chung=trieu_chung,
            chan_doan=chan_doan,
            huong_dieu_tri=huong_dieu_tri
        )


        lich.trang_thai = "xong"
        lich.save()


        messages.success(request, "Đã hoàn thành khám")

        return redirect("doctor_dashboard")


    return render(request, "core/doctor_exam.html", {
        "lich": lich
    })


# ==========================
# ĐĂNG KÝ
# ==========================
def register(request):

    if request.method == "POST":
        action = request.POST.get("action", "update_profile")
        if action == "change_password":
            current_password = request.POST.get("current_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if not current_password or not new_password or not confirm_password:
                messages.error(request, "Vui lòng nhập đầy đủ thông tin đổi mật khẩu.")
                return redirect("profile")

            if not request.user.check_password(current_password):
                messages.error(request, "Mật khẩu hiện tại không đúng.")
                return redirect("profile")

            if new_password != confirm_password:
                messages.error(request, "Mật khẩu xác nhận không khớp.")
                return redirect("profile")

            try:
                validate_password(new_password, user=request.user)
            except ValidationError as exc:
                for err in exc.messages:
                    messages.error(request, err)
                return redirect("profile")

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Đổi mật khẩu thành công.")
            return redirect("profile")

        username = request.POST["username"]
        password = request.POST["password"]
        name = request.POST["name"]
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Vui lòng nhập email")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email đã được sử dụng")
            return redirect("register")

        if User.objects.filter(username=username).exists():

            messages.error(request, "Tài khoản đã tồn tại")

            return redirect("register")


        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )


        BenhNhan.objects.create(
            ho_ten=name,
            so_dien_thoai=username,
            ngay_sinh="2000-01-01",
            gioi_tinh="nam",
            dia_chi="Chưa cập nhật"
        )


        messages.success(request, "Đăng ký thành công")

        return redirect("login")


    return render(request, "core/register.html")


# ==========================
# ĐĂNG NHẬP
# ==========================
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)

            # Nếu là bác sĩ
            if hasattr(user, "bac_si"):
                return redirect("bac_si_home")

            # Nếu là bệnh nhân
            return redirect("home")

        messages.error(request, "Sai tài khoản hoặc mật khẩu")

    return render(request, "core/login.html")


# ==========================
# ĐĂNG XUẤT
# ==========================
def user_logout(request):

    logout(request)

    return redirect("login")

# ==========================
# QUÊN MẬT KHẨU (SĐT + EMAIL)
# ==========================
def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not username or not email or not new_password or not confirm_password:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin")
            return redirect("forgot_password")

        if new_password != confirm_password:
            messages.error(request, "Mật khẩu xác nhận không khớp")
            return redirect("forgot_password")

        user = User.objects.filter(username=username, email=email).first()
        if not user:
            messages.error(request, "SĐT hoặc email không đúng")
            return redirect("forgot_password")

        user.set_password(new_password)
        user.save()

        messages.success(request, "Đổi mật khẩu thành công. Vui lòng đăng nhập lại")
        return redirect("login")

    return render(request, "core/forgot_password.html")

# ==========================
# TRANG CHỦ BÁC SĨ
# ==========================
@login_required
def bac_si_home(request):

    try:
        bac_si = request.user.bac_si
    except:
        return redirect("home")

    lich_khams = bac_si.lich_khams.all().order_by("-ngay_kham")

    return render(request, "core/bac_si_home.html", {
        "bac_si": bac_si,
        "lich_khams": lich_khams
    })
 
# ==========================
# HỒ SƠ NGƯỜI DÙNG
# ==========================
@login_required
def profile(request):

    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Không tìm thấy hồ sơ"
        })

    if request.method == "POST":

        so_dien_thoai_moi = request.POST.get("so_dien_thoai", "").strip()
        if so_dien_thoai_moi and so_dien_thoai_moi != request.user.username:
            if User.objects.filter(username=so_dien_thoai_moi).exclude(pk=request.user.pk).exists():
                messages.error(request, "Số điện thoại đã được sử dụng cho tài khoản khác")
                return redirect("profile")
            request.user.username = so_dien_thoai_moi
            request.user.save()

        benh_nhan.ho_ten = request.POST["ho_ten"]
        benh_nhan.ngay_sinh = request.POST["ngay_sinh"]
        benh_nhan.gioi_tinh = request.POST["gioi_tinh"]
        benh_nhan.dia_chi = request.POST["dia_chi"]
        if so_dien_thoai_moi:
            benh_nhan.so_dien_thoai = so_dien_thoai_moi

        # BHYT
        ma_bhyt = request.POST.get("ma_bhyt", "").strip()
        ngay_cap = request.POST.get("ngay_cap", "").strip()
        ngay_het_han = request.POST.get("ngay_het_han", "").strip()

        if ma_bhyt:
            if not ngay_cap or not ngay_het_han:
                messages.error(request, "Vui lòng nhập ngày cấp và ngày hết hạn của BHYT")
                return redirect("profile")

            bhyt, created = BaoHiemYTe.objects.get_or_create(
                ma_bhyt=ma_bhyt,
                defaults={
                    "ngay_cap": ngay_cap,
                    "ngay_het_han": ngay_het_han,
                },
            )

            if not created and (
                str(bhyt.ngay_cap) != ngay_cap or str(bhyt.ngay_het_han) != ngay_het_han
            ):
                bhyt.ngay_cap = ngay_cap
                bhyt.ngay_het_han = ngay_het_han
                bhyt.save()

            benh_nhan.bhyt = bhyt

        benh_nhan.save()

        messages.success(request, "Cập nhật thành công")

        return redirect("profile")

    return render(request, "core/profile.html", {
        "bn": benh_nhan
    })


# ==========================
# THÔNG BÁO (BỆNH NHÂN)
# ==========================
@login_required
def notifications(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mark_all":
            ThongBao.objects.filter(
                nguoi_nhan=request.user,
                da_doc=False,
            ).update(da_doc=True)
            messages.success(request, "Đã đánh dấu tất cả thông báo là đã đọc.")
            return redirect("notifications")
        if action == "mark_one":
            tb_id = request.POST.get("tb_id")
            if tb_id:
                ThongBao.objects.filter(
                    nguoi_nhan=request.user,
                    id=tb_id,
                ).update(da_doc=True)
            return redirect("notifications")

    thong_baos = ThongBao.objects.filter(
        nguoi_nhan=request.user
    ).order_by("-thoi_gian")

    return render(request, "core/notifications.html", {
        "thong_baos": thong_baos,
    })
