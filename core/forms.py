import datetime
import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

from .models import BacSi, BenhNhan, BenhVien, GioLamViecBacSi, Khoa, LichKham


def _translate_password_validation_message(message):
    mapping = {
        "This password is too short. It must contain at least 8 characters.": "Mật khẩu quá ngắn. Mật khẩu phải có ít nhất 8 ký tự.",
        "This password is too common.": "Mật khẩu quá phổ biến, vui lòng chọn mật khẩu khác an toàn hơn.",
        "This password is entirely numeric.": "Mật khẩu không được chỉ gồm chữ số.",
        "The password is too similar to the username.": "Mật khẩu quá giống với tên người dùng.",
    }
    return mapping.get(message, message)


class DatLichForm(forms.ModelForm):
    class Meta:
        model = LichKham
        fields = ["bac_si", "ngay_kham", "gio_kham", "ghi_chu"]
        error_messages = {
            "ngay_kham": {
                "required": "Vui lÃ²ng chá»n ngÃ y khÃ¡m.",
                "invalid": "NgÃ y khÃ¡m khÃ´ng há»£p lá»‡.",
            },
            "gio_kham": {
                "required": "Vui lÃ²ng chá»n giá» khÃ¡m.",
                "invalid": "Giá» khÃ¡m khÃ´ng há»£p lá»‡.",
            },
        }

        widgets = {
            "ngay_kham": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "gio_kham": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control",
                "step": "1800",
                "min": "00:00",
                "max": "23:30",
            }),
            "ghi_chu": forms.Textarea(attrs={
                "rows": 3,
                "class": "form-control",
            }),
        }

    bac_si = forms.ModelChoiceField(
        queryset=BacSi.objects.none(),
        widget=forms.Select(attrs={"class": "form-control"}),
        error_messages={
            "required": "Vui lÃ²ng chá»n bÃ¡c sÄ©.",
            "invalid_choice": "BÃ¡c sÄ© Ä‘Ã£ chá»n khÃ´ng há»£p lá»‡.",
        },
    )
    ghi_chu = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        error_messages={
            "required": "Vui lòng nhập ghi chú.",
        },
    )

    def clean_gio_kham(self):
        gio_kham = self.cleaned_data.get("gio_kham")
        if gio_kham and (
            gio_kham.minute not in {0, 30}
            or gio_kham.second != 0
            or gio_kham.microsecond != 0
        ):
            raise forms.ValidationError("Giá» khÃ¡m chá»‰ nháº­n cÃ¡c má»‘c 30 phÃºt (00 hoáº·c 30).")
        return gio_kham

    def clean_ghi_chu(self):
        ghi_chu = (self.cleaned_data.get("ghi_chu") or "").strip()
        if not ghi_chu:
            raise forms.ValidationError("Vui lòng nhập ghi chú.")
        return ghi_chu


class ContactFeedbackForm(forms.Form):
    ho_ten = forms.CharField(
        max_length=120,
        label="Há» tÃªn",
        error_messages={
            "required": "Vui lÃ²ng nháº­p há» tÃªn.",
            "max_length": "Há» tÃªn tá»‘i Ä‘a 120 kÃ½ tá»±.",
        },
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nguyá»…n VÄƒn A"}),
    )
    email = forms.EmailField(
        label="Email liÃªn há»‡",
        error_messages={
            "required": "Vui lÃ²ng nháº­p email liÃªn há»‡.",
            "invalid": "Email khÃ´ng Ä‘Ãºng Ä‘á»‹nh dáº¡ng.",
        },
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "ban@email.com"}),
    )
    chu_de = forms.CharField(
        max_length=180,
        label="Chá»§ Ä‘á»",
        error_messages={
            "required": "Vui lÃ²ng nháº­p chá»§ Ä‘á».",
            "max_length": "Chá»§ Ä‘á» tá»‘i Ä‘a 180 kÃ½ tá»±.",
        },
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "GÃ³p Ã½ vá» chá»©c nÄƒng Ä‘áº·t lá»‹ch"}),
    )
    noi_dung = forms.CharField(
        min_length=10,
        label="Ná»™i dung gÃ³p Ã½",
        error_messages={
            "required": "Vui lÃ²ng nháº­p ná»™i dung gÃ³p Ã½.",
            "min_length": "Ná»™i dung gÃ³p Ã½ tá»‘i thiá»ƒu 10 kÃ½ tá»±.",
        },
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Nháº­p gÃ³p Ã½ hoáº·c váº¥n Ä‘á» báº¡n gáº·p...",
            }
        ),
    )


class AdminBenhVienForm(forms.ModelForm):
    lat = forms.FloatField(
        min_value=-90,
        max_value=90,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
        label="VÄ© Ä‘á»™",
    )
    lon = forms.FloatField(
        min_value=-180,
        max_value=180,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
        label="Kinh Ä‘á»™",
    )

    class Meta:
        model = BenhVien
        fields = [
            "ten",
            "dia_chi",
            "phuong",
            "lat",
            "lon",
            "cap_cuu_24h",
            "co_bhyt",
            "loai_hinh",
        ]
        labels = {
            "ten": "TÃªn bá»‡nh viá»‡n",
            "dia_chi": "Äá»‹a chá»‰",
            "phuong": "PhÆ°á»ng",
            "cap_cuu_24h": "Cáº¥p cá»©u 24/7",
            "co_bhyt": "CÃ³ BHYT",
            "loai_hinh": "Loáº¡i hÃ¬nh",
        }
        widgets = {
            "ten": forms.TextInput(attrs={"class": "form-control"}),
            "dia_chi": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "phuong": forms.TextInput(attrs={"class": "form-control"}),
            "cap_cuu_24h": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "co_bhyt": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "loai_hinh": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.vi_tri:
            self.fields["lat"].initial = self.instance.vi_tri.y
            self.fields["lon"].initial = self.instance.vi_tri.x

    def clean(self):
        cleaned_data = super().clean()
        cap_cuu_24h = bool(cleaned_data.get("cap_cuu_24h"))
        # Keep backward-compatible field in sync while UI only exposes 24/7.
        cleaned_data["co_cap_cuu"] = cap_cuu_24h
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        lat = self.cleaned_data.get("lat")
        lon = self.cleaned_data.get("lon")
        obj.vi_tri = Point(lon, lat, srid=4326)
        obj.co_cap_cuu = bool(self.cleaned_data.get("cap_cuu_24h"))
        # Keep required model fields consistent while admin now manages
        # detailed operating hours via schedule-by-week table.
        if not obj.gio_mo:
            obj.gio_mo = datetime.time(7, 0)
        if not obj.gio_dong:
            obj.gio_dong = datetime.time(17, 0)
        if commit:
            obj.save()
        return obj


class AdminKhoaForm(forms.ModelForm):
    class Meta:
        model = Khoa
        fields = ["ten", "benh_vien"]
        widgets = {
            "ten": forms.TextInput(attrs={"class": "form-control"}),
            "benh_vien": forms.Select(attrs={"class": "form-control"}),
        }


class AdminBacSiForm(forms.ModelForm):
    class Meta:
        model = BacSi
        fields = ["ho_ten", "so_dien_thoai", "chuyen_khoa", "benh_vien", "khoa", "user"]
        widgets = {
            "ho_ten": forms.TextInput(attrs={"class": "form-control"}),
            "so_dien_thoai": forms.TextInput(attrs={"class": "form-control"}),
            "chuyen_khoa": forms.TextInput(attrs={"class": "form-control"}),
            "benh_vien": forms.Select(attrs={"class": "form-control"}),
            "khoa": forms.Select(attrs={"class": "form-control"}),
            "user": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["khoa"].queryset = Khoa.objects.none()
        self.fields["user"].required = False
        self.fields["user"].label = "TÃ i khoáº£n liÃªn káº¿t (tÃ¹y chá»n)"

        benh_vien_id = None
        if self.is_bound:
            benh_vien_id = self.data.get("benh_vien")
        elif self.instance and self.instance.pk:
            benh_vien_id = self.instance.benh_vien_id

        if benh_vien_id:
            try:
                self.fields["khoa"].queryset = Khoa.objects.filter(benh_vien_id=int(benh_vien_id)).order_by("ten")
            except (TypeError, ValueError):
                self.fields["khoa"].queryset = Khoa.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        benh_vien = cleaned_data.get("benh_vien")
        khoa = cleaned_data.get("khoa")
        if benh_vien and khoa and khoa.benh_vien_id != benh_vien.id:
            self.add_error("khoa", "Khoa khÃ´ng thuá»™c bá»‡nh viá»‡n Ä‘Ã£ chá»n.")
        return cleaned_data


class AdminGioLamViecBacSiForm(forms.ModelForm):
    class Meta:
        model = GioLamViecBacSi
        fields = "__all__"
        widgets = {
            "bac_si": forms.Select(attrs={"class": "form-control"}),
            "thu": forms.Select(attrs={"class": "form-control"}),
            "gio_bat_dau": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "gio_ket_thuc": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "nghi": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bac_si"].queryset = BacSi.objects.select_related("benh_vien").order_by("ho_ten")
        self.fields["bac_si"].label_from_instance = (
            lambda obj: f"{obj.ho_ten} - {obj.benh_vien.ten}"
        )


class AdminUserForm(forms.ModelForm):
    ROLE_USER = "nguoi_dung"
    ROLE_DOCTOR = "bac_si"
    ROLE_ADMIN = "admin"

    role = forms.ChoiceField(
        required=True,
        label="Vai trò",
        choices=(
            (ROLE_USER, "Người dùng"),
            (ROLE_DOCTOR, "Bác sĩ"),
            (ROLE_ADMIN, "Admin"),
        ),
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Bác sĩ phải được liên kết trong danh mục Bác sĩ.",
    )

    password = forms.CharField(
        required=False,
        label="Mật khẩu mới",
        widget=forms.PasswordInput(render_value=False, attrs={"class": "form-control"}),
        help_text="Để trống nếu không đổi mật khẩu.",
    )

    so_dien_thoai = forms.CharField(
        required=False,
        label="Số điện thoại",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Đồng bộ với hồ sơ bệnh nhân của tài khoản này.",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "so_dien_thoai",
            "is_active",
            "role",
            "password",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._benh_nhan_instance = None

        if self.instance and self.instance.pk:
            if self.instance.is_staff or self.instance.is_superuser:
                self.fields["role"].initial = self.ROLE_ADMIN
            elif BacSi.objects.filter(user=self.instance).exists():
                self.fields["role"].initial = self.ROLE_DOCTOR
            else:
                self.fields["role"].initial = self.ROLE_USER

            benh_nhan = BenhNhan.objects.filter(user=self.instance).first()
            if benh_nhan:
                self.fields["so_dien_thoai"].initial = benh_nhan.so_dien_thoai
                self._benh_nhan_instance = benh_nhan
        else:
            self.fields["role"].initial = self.ROLE_USER

        if not self.instance or not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = "Bắt buộc khi tạo tài khoản."

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        current_user = self.instance if self.instance and self.instance.pk else None
        has_doctor_profile = bool(current_user and BacSi.objects.filter(user=current_user).exists())

        if role == self.ROLE_DOCTOR and not has_doctor_profile:
            self.add_error(
                "role",
                "Tài khoản này chưa liên kết bác sĩ. Hãy vào danh mục Bác sĩ để liên kết trước.",
            )

        if role in {self.ROLE_USER, self.ROLE_ADMIN} and has_doctor_profile:
            self.add_error(
                "role",
                "Tài khoản đang liên kết Bác sĩ. Hãy gỡ liên kết ở danh mục Bác sĩ nếu muốn đổi vai trò.",
            )

        so_dien_thoai = (cleaned_data.get("so_dien_thoai") or "").strip()
        if so_dien_thoai:
            if not re.fullmatch(r"^0\d{9}$", so_dien_thoai):
                self.add_error("so_dien_thoai", "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng số 0.")
            else:
                qs = BenhNhan.objects.filter(so_dien_thoai=so_dien_thoai)
                if self._benh_nhan_instance:
                    qs = qs.exclude(pk=self._benh_nhan_instance.pk)
                if qs.exists():
                    self.add_error("so_dien_thoai", "Số điện thoại đã được sử dụng.")

        raw_password = (cleaned_data.get("password") or "").strip()
        if raw_password:
            user_for_validation = self.instance if self.instance and self.instance.pk else User(
                username=(cleaned_data.get("username") or "").strip(),
                email=(cleaned_data.get("email") or "").strip(),
            )
            try:
                validate_password(raw_password, user=user_for_validation)
            except ValidationError as exc:
                for message in exc.messages:
                    self.add_error("password", _translate_password_validation_message(message))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get("role", self.ROLE_USER)
        if role == self.ROLE_ADMIN:
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False

        raw_password = self.cleaned_data.get("password", "").strip()
        if raw_password:
            user.set_password(raw_password)
        elif not user.pk:
            user.set_unusable_password()

        if commit:
            user.save()
            so_dien_thoai = (self.cleaned_data.get("so_dien_thoai") or "").strip()
            benh_nhan = self._benh_nhan_instance or BenhNhan.objects.filter(user=user).first()
            if benh_nhan:
                if so_dien_thoai:
                    benh_nhan.so_dien_thoai = so_dien_thoai
                benh_nhan.user = user
                benh_nhan.save(update_fields=["so_dien_thoai", "user"])

        return user





