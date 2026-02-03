from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import BaoHiemYTe

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

    khoas = benh_vien.khoas.all()

    khoa_id = request.GET.get("khoa")

    bac_sis = None

    if khoa_id:
        bac_sis = benh_vien.bac_sis.filter(khoa_id=khoa_id)

    if request.method == "POST":

        form = DatLichForm(request.POST)

        if khoa_id:
            form.fields["bac_si"].queryset = bac_sis

        if form.is_valid():

            lich = form.save(commit=False)
            lich.benh_nhan = benh_nhan
            lich.save()

            messages.success(request, "Đặt lịch thành công")

            return redirect("home")

    else:

        form = DatLichForm()

        if khoa_id:
            form.fields["bac_si"].queryset = bac_sis
        else:
            form.fields["bac_si"].queryset = BacSi.objects.none()

    return render(request, "core/dat_lich.html", {
        "form": form,
        "benh_vien": benh_vien,
        "khoas": khoas,
        "bac_sis": bac_sis,
        "khoa_id": khoa_id
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
