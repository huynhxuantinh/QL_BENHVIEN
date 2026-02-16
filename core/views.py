from django.shortcuts import render, get_object_or_404, redirect
import datetime
import math
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from .models import BaoHiemYTe

from .models import (
    BenhVien,
    BenhNhan,
    BacSi,
    GioLamViecBenhVien,
    GioLamViecBacSi,
    LichKham,
    LichSuKhamBenh,
    PhieuKham,
    LogHeThong,
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
    doctor_info = None
    doctor_today = []
    user_lat = None
    user_lon = None
    radius_km = None
    # GIS filters: open/emergency/BHYT + distance/radius + map markers
    filter_open = request.GET.get("open") == "1"
    filter_emergency = request.GET.get("emergency") == "1"
    filter_bhyt = request.GET.get("bhyt") == "1"
    filter_cap_cuu = request.GET.get("cap_cuu") == "1"
    loai_hinh = request.GET.get("loai_hinh")
    quan_filter = request.GET.get("quan")
    search_query = request.GET.get("q", "").strip()

    all_quan = (
        BenhVien.objects.values_list("quan", flat=True)
        .distinct()
        .order_by("quan")
    )

    lat_str = request.GET.get("lat")
    lon_str = request.GET.get("lon")
    radius_str = request.GET.get("radius")

    user_point = None
    if lat_str and lon_str:
        try:
            user_lat = float(lat_str)
            user_lon = float(lon_str)
            if -90 <= user_lat <= 90 and -180 <= user_lon <= 180:
                # GIS: build user location (SRID 4326) for distance/radius filtering
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

    if loai_hinh in {"cong", "tu", "qt"}:
        bvs = bvs.filter(loai_hinh=loai_hinh)
    else:
        loai_hinh = None

    if quan_filter:
        bvs = bvs.filter(quan=quan_filter)
    if search_query:
        bvs = bvs.filter(
            Q(ten__icontains=search_query)
            | Q(dia_chi__icontains=search_query)
            | Q(quan__icontains=search_query)
        )

    if request.user.is_authenticated:
        unread_count = ThongBao.objects.filter(
            nguoi_nhan=request.user,
            da_doc=False,
        ).count()
        try:
            bac_si = request.user.bac_si
        except BacSi.DoesNotExist:
            bac_si = None
        if bac_si:
            display_name = bac_si.ho_ten
            doctor_info = {
                "khoa": bac_si.khoa.ten,
                "benh_vien": bac_si.benh_vien.ten,
            }
            today = timezone.localdate()
            doctor_today = list(
                LichKham.objects.filter(
                    bac_si=bac_si,
                    ngay_kham=today,
                )
                .select_related("benh_nhan")
                .order_by("gio_kham")
            )
            for lich in doctor_today:
                lich.ca_label = "Ca sáng" if lich.gio_kham < datetime.time(12, 0) else "Ca chiều"
        else:
            benh_nhan = BenhNhan.objects.filter(
                so_dien_thoai=request.user.username
            ).only("ho_ten").first()
            display_name = benh_nhan.ho_ten if benh_nhan else request.user.username

    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_string_without_page = query_params.urlencode()

    def paginate_hospitals(items):
        paginator = Paginator(items, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        return paginator, page_obj, list(page_obj.object_list)

    now = timezone.localtime()
    time_bucket = now.strftime("%Y%m%d%H%M")
    cache_key = (
        f"home_filter:"
        f"lat={user_lat}|lon={user_lon}|radius={radius_km}|"
        f"open={int(filter_open)}|emg={int(filter_emergency)}|"
        f"bhyt={int(filter_bhyt)}|capcuu={int(filter_cap_cuu)}|"
        f"loai={loai_hinh or 'all'}|quan={quan_filter or 'all'}|q={search_query.lower()}|t={time_bucket}"
    )
    cached = cache.get(cache_key)
    if cached:
        ids = cached.get("ids", [])
        computed_map = cached.get("computed", {})
        bvs_qs = BenhVien.objects.filter(id__in=ids).prefetch_related("gio_lam_viecs")
        bvs_map = {bv.id: bv for bv in bvs_qs}
        cached_bvs = []
        for bv_id in ids:
            bv = bvs_map.get(bv_id)
            if not bv:
                continue
            info = computed_map.get(str(bv_id)) or computed_map.get(bv_id, {})
            bv.map_lat = info.get("map_lat")
            bv.map_lon = info.get("map_lon")
            bv.is_open = info.get("is_open", False)
            bv.emergency_active = info.get("emergency_active", False)
            bv.distance_km = info.get("distance_km")
            cached_bvs.append(bv)
        bvs = cached_bvs

        total_bvs = len(bvs)
        paginator, page_obj, paged_bvs = paginate_hospitals(bvs)

        map_data = []
        for bv in paged_bvs:
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
            "bvs": paged_bvs,
            "total_bvs": total_bvs,
            "paginator": paginator,
            "page_obj": page_obj,
            "query_string_without_page": query_string_without_page,
            "unread_count": unread_count,
            "display_name": display_name,
            "doctor_info": doctor_info,
            "doctor_today": doctor_today,
            "user_lat": user_lat,
            "user_lon": user_lon,
            "radius_km": radius_km,
            "filter_bhyt": filter_bhyt,
            "filter_cap_cuu": filter_cap_cuu,
            "filter_open": filter_open,
            "filter_emergency": filter_emergency,
            "loai_hinh": loai_hinh,
            "quan_filter": quan_filter,
            "q": search_query,
            "all_quan": all_quan,
            "map_data": map_data,
        })

    if filter_bhyt:
        bvs = bvs.filter(co_bhyt=True)
    if filter_cap_cuu:
        bvs = bvs.filter(co_cap_cuu=True)

    if user_point:
        # GIS: annotate distance from user, filter by radius, sort nearest first
        bvs = bvs.annotate(distance_m=Distance("vi_tri", user_point, spheroid=False))
        if radius_km:
            bvs = bvs.filter(distance_m__lte=radius_km * 1000)
        bvs = bvs.order_by("distance_m")

    def point_to_latlon(point):
        # GIS: convert Point to lat/lon (handle Web Mercator or WGS84)
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
        if hasattr(bv, "distance_m") and bv.distance_m is not None:
            if hasattr(bv.distance_m, "km"):
                distance_km = round(bv.distance_m.km, 2)
            elif hasattr(bv.distance_m, "m"):
                distance_km = round(bv.distance_m.m / 1000.0, 2)
            else:
                distance_km = round(float(bv.distance_m) / 1000.0, 2)
        setattr(bv, "distance_km", distance_km)
        if filter_open and not bv.is_open:
            continue
        if filter_emergency and not bv.emergency_active:
            continue
        computed_bvs.append(bv)

    if user_point:
        computed_bvs.sort(
            key=lambda item: (
                item.distance_km is None,
                item.distance_km if item.distance_km is not None else 1e9,
                item.ten.lower(),
            )
        )
    else:
        computed_bvs.sort(
            key=lambda item: (
                not getattr(item, "is_open", False),
                item.ten.lower(),
            )
        )
    bvs = computed_bvs

    total_bvs = len(bvs)
    paginator, page_obj, paged_bvs = paginate_hospitals(bvs)

    map_data = []
    for bv in paged_bvs:
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

    computed_payload = {}
    for bv in bvs:
        computed_payload[str(bv.id)] = {
            "map_lat": getattr(bv, "map_lat", None),
            "map_lon": getattr(bv, "map_lon", None),
            "is_open": getattr(bv, "is_open", False),
            "emergency_active": getattr(bv, "emergency_active", False),
            "distance_km": getattr(bv, "distance_km", None),
        }
    cache.set(cache_key, {
        "ids": [bv.id for bv in bvs],
        "computed": computed_payload,
    }, timeout=60)

    return render(request, "core/home.html", {
        "bvs": paged_bvs,
        "total_bvs": total_bvs,
        "paginator": paginator,
        "page_obj": page_obj,
        "query_string_without_page": query_string_without_page,
        "unread_count": unread_count,
        "display_name": display_name,
        "doctor_info": doctor_info,
        "doctor_today": doctor_today,
        "user_lat": user_lat,
        "user_lon": user_lon,
        "radius_km": radius_km,
        "filter_bhyt": filter_bhyt,
        "filter_cap_cuu": filter_cap_cuu,
        "filter_open": filter_open,
        "filter_emergency": filter_emergency,
        "loai_hinh": loai_hinh,
        "quan_filter": quan_filter,
        "q": search_query,
        "all_quan": all_quan,
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
            "msg": "B?n ch?a c? h? s? b?nh nh?n"
        })

    khoas = benh_vien.khoas.all().order_by("ten")
    khoa_id = (request.POST.get("khoa") or request.GET.get("khoa") or "").strip()

    selected_khoa = None
    if khoa_id:
        selected_khoa = benh_vien.khoas.filter(id=khoa_id).first()
        if not selected_khoa:
            khoa_id = ""

    bac_sis = benh_vien.bac_sis.none()
    bac_si_schedules = []
    if selected_khoa:
        bac_sis = benh_vien.bac_sis.filter(khoa=selected_khoa).prefetch_related("gio_lam_viecs")
        bac_si_schedules = [
            {
                "bac_si": bs,
                "gio_lam_viecs": bs.gio_lam_viecs.all().order_by("thu"),
            }
            for bs in bac_sis
        ]

    if request.method == "POST":
        form = DatLichForm(request.POST)
        form.fields["bac_si"].queryset = bac_sis

        if not selected_khoa:
            form.add_error(None, "Vui l?ng ch?n khoa tr??c khi ??t l?ch.")
            messages.error(request, "Kh?ng th? ??t l?ch. Vui l?ng ki?m tra l?i th?ng tin.")
            return render(request, "core/appointment.html", {
                "form": form,
                "benh_vien": benh_vien,
                "benh_nhan": benh_nhan,
                "khoas": khoas,
                "bac_sis": bac_sis,
                "bac_si_schedules": bac_si_schedules,
                "khoa_id": khoa_id,
            })

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
                messages.error(request, "Kh?ng th? ??t l?ch. Vui l?ng ki?m tra l?i th?ng tin.")
                return render(request, "core/appointment.html", {
                    "form": form,
                    "benh_vien": benh_vien,
                    "benh_nhan": benh_nhan,
                    "khoas": khoas,
                    "bac_sis": bac_sis,
                    "bac_si_schedules": bac_si_schedules,
                    "khoa_id": khoa_id,
                })
            except IntegrityError:
                form.add_error("ngay_kham", "B?n ?? c? l?ch kh?m trong ng?y n?y.")
                messages.error(request, "Kh?ng th? ??t l?ch. Vui l?ng ki?m tra l?i th?ng tin.")
                return render(request, "core/appointment.html", {
                    "form": form,
                    "benh_vien": benh_vien,
                    "benh_nhan": benh_nhan,
                    "khoas": khoas,
                    "bac_sis": bac_sis,
                    "bac_si_schedules": bac_si_schedules,
                    "khoa_id": khoa_id,
                })

            messages.success(request, "??t l?ch th?nh c?ng.")
            ThongBao.objects.create(
                nguoi_nhan=request.user,
                loai="lich_kham",
                tieu_de="??t l?ch th?nh c?ng",
                noi_dung=(
                    f"T?o l?ch kh?m v?o ng?y {lich.ngay_kham} l?c {lich.gio_kham} v?i b?c s? {lich.bac_si.ho_ten}."
                ),
                lien_ket="/lich-kham-sap-toi/",
            )
            return redirect("upcoming_appointments")

        messages.error(request, "Kh?ng th? ??t l?ch. Vui l?ng ki?m tra l?i th?ng tin.")
    else:
        form = DatLichForm()
        form.fields["bac_si"].queryset = bac_sis

    return render(request, "core/appointment.html", {
        "form": form,
        "benh_vien": benh_vien,
        "benh_nhan": benh_nhan,
        "khoas": khoas,
        "bac_sis": bac_sis,
        "bac_si_schedules": bac_si_schedules,
        "khoa_id": khoa_id,
    })


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
    try:
        bac_si = request.user.bac_si
    except BacSi.DoesNotExist:
        bac_si = None

    if bac_si:
        phieu = get_object_or_404(
            PhieuKham,
            id=phieu_id,
            lich_kham__bac_si=bac_si,
        )
        edit_logs = LogHeThong.objects.filter(
            model_name="PhieuKham",
            object_id=phieu.id,
            hanh_dong="update",
        ).select_related("nguoi_thuc_hien").order_by("-thoi_gian")

        return render(request, "core/exam_detail.html", {
            "benh_nhan": phieu.benh_nhan,
            "phieu": phieu,
            "edit_logs": edit_logs,
        })

    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "\u0042\u1ea1\u006e\u0020\u0063\u0068\u01b0\u0061\u0020\u0063\u00f3\u0020\u0068\u1ed3\u0020\u0073\u01a1\u0020\u0062\u1ec7\u006e\u0068\u0020\u006e\u0068\u00e2\u006e"
        })

    phieu = get_object_or_404(PhieuKham, id=phieu_id, benh_nhan=benh_nhan)

    edit_logs = LogHeThong.objects.filter(
        model_name="PhieuKham",
        object_id=phieu.id,
        hanh_dong="update",
    ).select_related("nguoi_thuc_hien").order_by("-thoi_gian")

    return render(request, "core/exam_detail.html", {
        "benh_nhan": benh_nhan,
        "phieu": phieu,
        "edit_logs": edit_logs,
    })


# ==========================
# DASHBOARD BÁC SĨ
# ==========================
@login_required
def doctor_dashboard(request):

    try:
        bac_si = request.user.bac_si
    except BacSi.DoesNotExist:
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
    except BacSi.DoesNotExist:
        return redirect("home")


    lich = get_object_or_404(
        LichKham,
        id=lich_id,
        bac_si=bac_si
    )

    if hasattr(lich, "phieu_kham"):
        messages.info(request, "\u004c\u1ecbch kh\u00e1m n\u00e0y \u0111\u00e3 c\u00f3 phi\u1ebfu kh\u00e1m.")
        return redirect("bac_si_home")


    if request.method == "POST":

        trieu_chung = request.POST.get("trieu_chung", "").strip()
        chan_doan = request.POST.get("chan_doan", "").strip()
        huong_dieu_tri = request.POST.get("huong_dieu_tri", "").strip()

        if not trieu_chung or not chan_doan or not huong_dieu_tri:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin phiếu khám.")
            return render(request, "core/doctor_exam.html", {
                "lich": lich
            })


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

        return redirect("bac_si_home")


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
    except BacSi.DoesNotExist:
        return redirect("home")

    status_filter = request.GET.get("status", "").strip()
    range_filter = request.GET.get("range", "").strip()
    shift_filter = request.GET.get("shift", "").strip()

    lich_khams = bac_si.lich_khams.all()

    today = timezone.localdate()
    today_qs = bac_si.lich_khams.filter(ngay_kham=today)
    stats = {
        "tong": today_qs.count(),
        "cho": today_qs.filter(trang_thai="cho").count(),
        "dang": today_qs.filter(trang_thai="dang").count(),
        "xong": today_qs.filter(trang_thai="xong").count(),
        "huy": today_qs.filter(trang_thai="huy").count(),
    }
    if status_filter in {"cho", "dang", "xong", "huy"}:
        lich_khams = lich_khams.filter(trang_thai=status_filter)
    else:
        status_filter = ""

    if range_filter in {"week", "month"}:
        if range_filter == "week":
            end_date = today + datetime.timedelta(days=7)
        else:
            end_date = today + datetime.timedelta(days=30)
        lich_khams = lich_khams.filter(ngay_kham__gte=today, ngay_kham__lte=end_date)
    else:
        range_filter = ""

    if shift_filter in {"sang", "chieu"}:
        noon = datetime.time(12, 0)
        if shift_filter == "sang":
            lich_khams = lich_khams.filter(gio_kham__lt=noon)
        else:
            lich_khams = lich_khams.filter(gio_kham__gte=noon)
    else:
        shift_filter = ""

    lich_khams = lich_khams.order_by("-ngay_kham", "-gio_kham")
    phieu_map = {
        phieu.lich_kham_id: phieu
        for phieu in PhieuKham.objects.filter(lich_kham__in=lich_khams)
    }
    for lich in lich_khams:
        lich.phieu_kham_obj = phieu_map.get(lich.id)
        lich.ca_label = "Ca sáng" if lich.gio_kham < datetime.time(12, 0) else "Ca chiều"

    return render(request, "core/doctor_home.html", {
        "bac_si": bac_si,
        "lich_khams": lich_khams,
        "status_filter": status_filter,
        "range_filter": range_filter,
        "shift_filter": shift_filter,
        "stats": stats,
    })


# ==========================
# HỒ SƠ BỆNH NHÂN (BÁC SĨ)
# ==========================
@login_required
def bac_si_patient_detail(request, benh_nhan_id):

    try:
        bac_si = request.user.bac_si
    except BacSi.DoesNotExist:
        return redirect("home")

    benh_nhan = get_object_or_404(BenhNhan, id=benh_nhan_id)

    co_lich = LichKham.objects.filter(
        bac_si=bac_si,
        benh_nhan=benh_nhan
    ).exists()
    if not co_lich:
        messages.error(request, "\u0042\u00e1\u0063\u0020\u0073\u0129\u0020\u006b\u0068\u00f4\u006e\u0067\u0020\u0063\u00f3\u0020\u006c\u1ecb\u0063\u0068\u0020\u006b\u0068\u00e1\u006d\u0020\u0076\u1edb\u0069\u0020\u0062\u1ec7\u006e\u0068\u0020\u006e\u0068\u00e2\u006e\u0020\u006e\u00e0\u0079\u002e")
        return redirect("bac_si_home")

    lich_su = LichSuKhamBenh.objects.filter(
        benh_nhan=benh_nhan
    ).select_related("bac_si", "benh_vien", "phieu_kham").order_by("-ngay_kham", "-ngay_tao")

    return render(request, "core/doctor_patient_detail.html", {
        "bac_si": bac_si,
        "benh_nhan": benh_nhan,
        "lich_su": lich_su,
    })


# ==========================
# BẮT ĐẦU KHÁM (BÁC SĨ)
# ==========================
@login_required
def start_exam(request, lich_id):
    if request.method != "POST":
        return redirect("bac_si_home")

    try:
        bac_si = request.user.bac_si
    except BacSi.DoesNotExist:
        return redirect("home")

    lich = get_object_or_404(
        LichKham,
        id=lich_id,
        bac_si=bac_si
    )

    if lich.trang_thai == "huy":
        messages.error(request, "\u004c\u1ecbch \u0111\u00e3 h\u1ee7y, kh\u00f4ng th\u1ec3 b\u1eaft \u0111\u1ea7u kh\u00e1m.")
        return redirect("bac_si_home")

    if lich.trang_thai == "xong":
        messages.info(request, "\u004c\u1ecbch \u0111\u00e3 ho\u00e0n th\u00e0nh.")
        return redirect("bac_si_home")

    if lich.trang_thai != "dang":
        lich.trang_thai = "dang"
        lich.save()
        messages.success(request, "\u0110\u00e3 chuy\u1ec3n tr\u1ea1ng th\u00e1i sang \u0111ang kh\u00e1m.")

    return redirect("bac_si_home")


# ==========================
# THÔNG BÁO BÁC SĨ
# ==========================
@login_required
def bac_si_notifications(request):
    try:
        request.user.bac_si
    except BacSi.DoesNotExist:
        return redirect("home")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mark_all":
            ThongBao.objects.filter(
                nguoi_nhan=request.user,
                da_doc=False,
            ).update(da_doc=True)
            messages.success(request, "\u0110\u00e3 \u0111\u00e1nh d\u1ea5u t\u1ea5t c\u1ea3 th\u00f4ng b\u00e1o l\u00e0 \u0111\u00e3 \u0111\u1ecdc.")
            return redirect("bac_si_notifications")
        if action == "mark_one":
            tb_id = request.POST.get("tb_id")
            if tb_id:
                ThongBao.objects.filter(
                    nguoi_nhan=request.user,
                    id=tb_id,
                ).update(da_doc=True)
            return redirect("bac_si_notifications")

    thong_baos = ThongBao.objects.filter(
        nguoi_nhan=request.user
    ).order_by("-thoi_gian")

    return render(request, "core/doctor_notifications.html", {
        "thong_baos": thong_baos,
    })
 
# ==========================
# LỊCH LÀM VIỆC BÁC SĨ
# ==========================
@login_required
def bac_si_schedule(request):
    try:
        bac_si = request.user.bac_si
    except BacSi.DoesNotExist:
        return redirect("home")

    thu_labels = [
        (0, "Chủ nhật"),
        (1, "Thứ 2"),
        (2, "Thứ 3"),
        (3, "Thứ 4"),
        (4, "Thứ 5"),
        (5, "Thứ 6"),
        (6, "Thứ 7"),
    ]

    if request.method == "POST":
        for thu, _ in thu_labels:
            nghi = request.POST.get(f"nghi_{thu}") == "on"
            gio_bat_dau = request.POST.get(f"gio_bat_dau_{thu}", "").strip()
            gio_ket_thuc = request.POST.get(f"gio_ket_thuc_{thu}", "").strip()

            if nghi:
                GioLamViecBacSi.objects.update_or_create(
                    bac_si=bac_si,
                    thu=thu,
                    defaults={
                        "nghi": True,
                        "gio_bat_dau": "00:00",
                        "gio_ket_thuc": "00:00",
                    },
                )
                continue

            if not gio_bat_dau or not gio_ket_thuc:
                messages.error(request, "\u0056\u0075\u0069\u0020\u006c\u00f2\u006e\u0067\u0020\u006e\u0068\u1ead\u0070\u0020\u0111\u1ea7\u0079\u0020\u0111\u1ee7\u0020\u0067\u0069\u1edd\u0020\u006c\u00e0\u006d\u0020\u0076\u0069\u1ec7\u0063\u002e")
                return redirect("bac_si_schedule")

            try:
                start_time = datetime.time.fromisoformat(gio_bat_dau)
                end_time = datetime.time.fromisoformat(gio_ket_thuc)
            except ValueError:
                messages.error(request, "\u0110\u1ecb\u006e\u0068\u0020\u0064\u1ea1\u006e\u0067\u0020\u0067\u0069\u1edd\u0020\u006b\u0068\u00f4\u006e\u0067\u0020\u0068\u1ee3\u0070\u0020\u006c\u1ec7\u002e")
                return redirect("bac_si_schedule")

            if start_time >= end_time:
                messages.error(request, "\u0047\u0069\u1edd\u0020\u0062\u1eaf\u0074\u0020\u0111\u1ea7\u0075\u0020\u0070\u0068\u1ea3\u0069\u0020\u006e\u0068\u1ecf\u0020\u0068\u01a1\u006e\u0020\u0067\u0069\u1edd\u0020\u006b\u1ebf\u0074\u0020\u0074\u0068\u00fa\u0063\u002e")
                return redirect("bac_si_schedule")

            GioLamViecBacSi.objects.update_or_create(
                bac_si=bac_si,
                thu=thu,
                defaults={
                    "nghi": False,
                    "gio_bat_dau": start_time,
                    "gio_ket_thuc": end_time,
                },
            )

        messages.success(request, "\u0110\u00e3 c\u1ead\u0070\u0020\u006e\u0068\u1ead\u0074\u0020\u006c\u1ecb\u0063\u0068\u0020\u006c\u00e0\u006d\u0020\u0076\u0069\u1ec7\u0063\u002e")
        return redirect("bac_si_schedule")

    schedules = {
        glv.thu: glv
        for glv in GioLamViecBacSi.objects.filter(bac_si=bac_si)
    }
    schedule_items = []
    for thu, label in thu_labels:
        glv = schedules.get(thu)
        schedule_items.append({
            "thu": thu,
            "label": label,
            "nghi": glv.nghi if glv else False,
            "gio_bat_dau": glv.gio_bat_dau.strftime("%H:%M") if glv and glv.gio_bat_dau else "",
            "gio_ket_thuc": glv.gio_ket_thuc.strftime("%H:%M") if glv and glv.gio_ket_thuc else "",
        })

    return render(request, "core/doctor_schedule.html", {
        "bac_si": bac_si,
        "schedule_items": schedule_items,
    })


# ==========================
# SỬA PHIẾU KHÁM (BÁC SĨ)
# ==========================
@login_required
def bac_si_phieu_kham_edit(request, phieu_id):
    try:
        bac_si = request.user.bac_si
    except BacSi.DoesNotExist:
        return redirect("home")

    phieu = get_object_or_404(
        PhieuKham,
        id=phieu_id,
        lich_kham__bac_si=bac_si,
    )

    if request.method == "POST":
        trieu_chung = request.POST.get("trieu_chung", "").strip()
        chan_doan = request.POST.get("chan_doan", "").strip()
        huong_dieu_tri = request.POST.get("huong_dieu_tri", "").strip()

        if not trieu_chung or not chan_doan or not huong_dieu_tri:
            messages.error(request, "\u0056\u0075\u0069\u0020\u006c\u00f2\u006e\u0067\u0020\u006e\u0068\u1ead\u0070\u0020\u0111\u1ea7\u0079\u0020\u0111\u1ee7\u0020\u0074\u0068\u00f4\u006e\u0067\u0020\u0074\u0069\u006e\u002e")
            return redirect("bac_si_phieu_kham_edit", phieu_id=phieu.id)

        old_data = {
            "trieu_chung": phieu.trieu_chung,
            "chan_doan": phieu.chan_doan,
            "huong_dieu_tri": phieu.huong_dieu_tri,
        }
        new_data = {
            "trieu_chung": trieu_chung,
            "chan_doan": chan_doan,
            "huong_dieu_tri": huong_dieu_tri,
        }

        phieu.trieu_chung = trieu_chung
        phieu.chan_doan = chan_doan
        phieu.huong_dieu_tri = huong_dieu_tri
        phieu.save()

        if old_data != new_data:
            LogHeThong.objects.create(
                model_name="PhieuKham",
                object_id=phieu.id,
                hanh_dong="update",
                du_lieu_cu=old_data,
                du_lieu_moi=new_data,
                nguoi_thuc_hien=request.user,
                ghi_chu="Cap nhat phieu kham",
            )

        messages.success(request, "\u0110\u00e3 c\u1ead\u0070\u0020\u006e\u0068\u1ead\u0074\u0020\u0070\u0068\u0069\u1ebf\u0075\u0020\u006b\u0068\u00e1\u006d\u002e")
        return redirect("phieu_kham_detail", phieu_id=phieu.id)

    return render(request, "core/doctor_exam_edit.html", {
        "phieu": phieu,
    })


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
