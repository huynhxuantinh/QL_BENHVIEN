from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import BenhVien, BenhNhan
from .forms import DatLichForm


# Trang chủ
def home(request):
    bvs = BenhVien.objects.all()
    return render(request, "core/home.html", {
        "bvs": bvs
    })


# Chi tiết bệnh viện
def hospital_detail(request, id):
    bv = get_object_or_404(BenhVien, id=id)

    khoas = bv.khoas.all()
    bac_sis = bv.bac_sis.all()

    return render(request, "core/hospital_detail.html", {
        "bv": bv,
        "khoas": khoas,
        "bac_sis": bac_sis,
    })
@login_required
def dat_lich(request, bv_id):

    # Lấy bệnh viện
    benh_vien = get_object_or_404(BenhVien, id=bv_id)

    # Lấy bệnh nhân theo số điện thoại (username)
    benh_nhan = BenhNhan.objects.filter(
        so_dien_thoai=request.user.username
    ).first()

    # Chưa có hồ sơ
    if not benh_nhan:
        return render(request, "core/error.html", {
            "msg": "Bạn chưa có hồ sơ bệnh nhân"
        })

    # POST: gửi form
    if request.method == "POST":

        form = DatLichForm(request.POST)

        # Chỉ cho chọn bác sĩ thuộc bệnh viện này
        form.fields["bac_si"].queryset = benh_vien.bac_sis.all()

        if form.is_valid():

            lich = form.save(commit=False)

            # Gán bệnh nhân
            lich.benh_nhan = benh_nhan

            # Gán bệnh viện (nếu model có field benh_vien)
            # lich.benh_vien = benh_vien

            lich.save()

            messages.success(request, "Đặt lịch thành công")

            return redirect("home")

    # GET: hiển thị form
    else:

        form = DatLichForm()

        # Lọc bác sĩ theo bệnh viện
        form.fields["bac_si"].queryset = benh_vien.bac_sis.all()

    return render(request, "core/dat_lich.html", {
        "form": form,
        "benh_vien": benh_vien
    })


# Đăng ký
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

        # Tạo hồ sơ bệnh nhân
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


# Đăng nhập
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
            return redirect("home")

        messages.error(request, "Sai tài khoản hoặc mật khẩu")

    return render(request, "core/login.html")


# Đăng xuất
def user_logout(request):
    logout(request)
    return redirect("login")
