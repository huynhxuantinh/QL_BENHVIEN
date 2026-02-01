from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import (
    BenhVien,
    BenhNhan,
    BacSi,
    LichKham,
    PhieuKham
)

from .forms import DatLichForm


# ==========================
# TRANG CHỦ
# ==========================
def home(request):

    bvs = BenhVien.objects.all()

    return render(request, "core/home.html", {
        "bvs": bvs
    })


# ==========================
# CHI TIẾT BỆNH VIỆN
# ==========================
def hospital_detail(request, id):

    bv = get_object_or_404(BenhVien, id=id)

    khoas = bv.khoas.all()
    bac_sis = bv.bac_sis.all()

    return render(request, "core/hospital_detail.html", {
        "bv": bv,
        "khoas": khoas,
        "bac_sis": bac_sis,
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


    if request.method == "POST":

        form = DatLichForm(request.POST)

        # Lọc bác sĩ theo bệnh viện
        form.fields["bac_si"].queryset = benh_vien.bac_sis.all()

        if form.is_valid():

            lich = form.save(commit=False)

            lich.benh_nhan = benh_nhan
            lich.save()

            messages.success(request, "Đặt lịch thành công")

            return redirect("home")

    else:

        form = DatLichForm()

        form.fields["bac_si"].queryset = benh_vien.bac_sis.all()


    return render(request, "core/dat_lich.html", {
        "form": form,
        "benh_vien": benh_vien
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

        username = request.POST["username"]
        password = request.POST["password"]
        name = request.POST["name"]


        if User.objects.filter(username=username).exists():

            messages.error(request, "Tài khoản đã tồn tại")

            return redirect("register")


        user = User.objects.create_user(
            username=username,
            password=password
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
