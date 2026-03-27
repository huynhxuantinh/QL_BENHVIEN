from django import forms
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from .models import BacSi, BenhVien, GioLamViecBacSi, Khoa, LichKham


class DatLichForm(forms.ModelForm):
    class Meta:
        model = LichKham
        fields = ["bac_si", "ngay_kham", "gio_kham", "ghi_chu"]

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
    )


class AdminBenhVienForm(forms.ModelForm):
    lat = forms.FloatField(
        min_value=-90,
        max_value=90,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
        label="\u0056\u0129 \u0111\u1ed9",
    )
    lon = forms.FloatField(
        min_value=-180,
        max_value=180,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
        label="Kinh \u0111\u1ed9",
    )

    class Meta:
        model = BenhVien
        fields = [
            "ten",
            "dia_chi",
            "quan",
            "lat",
            "lon",
            "co_cap_cuu",
            "cap_cuu_24h",
            "co_bhyt",
            "gio_mo",
            "gio_dong",
            "loai_hinh",
        ]
        labels = {
            "ten": "Tên bệnh viện",
            "dia_chi": "Địa chỉ",
            "quan": "Quận",
            "co_cap_cuu": "Có cấp cứu",
            "cap_cuu_24h": "Cấp cứu 24h",
            "co_bhyt": "Có BHYT",
            "gio_mo": "Giờ mở",
            "gio_dong": "Giờ đóng",
            "loai_hinh": "Loại hình",
        }
        widgets = {
            "ten": forms.TextInput(attrs={"class": "form-control"}),
            "dia_chi": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "quan": forms.TextInput(attrs={"class": "form-control"}),
            "co_cap_cuu": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cap_cuu_24h": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "co_bhyt": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "gio_mo": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "gio_dong": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "loai_hinh": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.vi_tri:
            self.fields["lat"].initial = self.instance.vi_tri.y
            self.fields["lon"].initial = self.instance.vi_tri.x

    def clean(self):
        cleaned_data = super().clean()
        cap_cuu_24h = cleaned_data.get("cap_cuu_24h")
        co_cap_cuu = cleaned_data.get("co_cap_cuu")
        if cap_cuu_24h and not co_cap_cuu:
            cleaned_data["co_cap_cuu"] = True
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        lat = self.cleaned_data.get("lat")
        lon = self.cleaned_data.get("lon")
        obj.vi_tri = Point(lon, lat, srid=4326)
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
        self.fields["user"].label = "Tài khoản liên kết (tùy chọn)"

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
            self.add_error("khoa", "Khoa kh\u00f4ng thu\u1ed9c b\u1ec7nh vi\u1ec7n \u0111\u00e3 ch\u1ecdn.")
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
    password = forms.CharField(
        required=False,
        label="Mật khẩu mới",
        widget=forms.PasswordInput(render_value=False, attrs={"class": "form-control"}),
        help_text="Để trống nếu không đổi mật khẩu.",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "password",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = "Bắt buộc khi tạo tài khoản."

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get("password", "").strip()
        if raw_password:
            user.set_password(raw_password)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
        return user
