from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

# ========================= 
# BỆNH VIỆN
# ========================= 
class BenhVien(models.Model):
    ten = models.CharField(max_length=255, db_index=True)
    dia_chi = models.TextField()
    quan = models.CharField(max_length=100, db_index=True)
    vi_tri = models.PointField(spatial_index=True)
    co_cap_cuu = models.BooleanField(default=False, db_index=True)
    cap_cuu_24h = models.BooleanField(default=False, db_index=True)
    co_bhyt = models.BooleanField(default=False, db_index=True)
    gio_mo = models.TimeField()
    gio_dong = models.TimeField()
    loai_hinh = models.CharField(
        max_length=10,
        choices=[
            ('cong', 'Công'),
            ('tu', 'Tư'),
            ('qt', 'Quốc tế'),
        ],
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['quan', 'co_cap_cuu']),
            models.Index(fields=['loai_hinh', 'co_bhyt']),
            models.Index(fields=['cap_cuu_24h', 'co_cap_cuu']),
        ]
        verbose_name = 'Bệnh viện'
        verbose_name_plural = 'Bệnh viện'

    def __str__(self):
        return self.ten


# ========================= 
# GIỜ LÀM VIỆC BỆNH VIỆN
# ========================= 
class GioLamViecBenhVien(models.Model):
    benh_vien = models.ForeignKey(
        BenhVien,
        on_delete=models.CASCADE,
        related_name='gio_lam_viecs'
    )
    thu = models.IntegerField(
        choices=[
            (0, 'Chủ nhật'),
            (1, 'Thứ 2'),
            (2, 'Thứ 3'),
            (3, 'Thứ 4'),
            (4, 'Thứ 5'),
            (5, 'Thứ 6'),
            (6, 'Thứ 7'),
        ],
        db_index=True
    )
    gio_mo = models.TimeField()
    gio_dong = models.TimeField()
    nghi = models.BooleanField(default=False)

    class Meta:
        unique_together = [['benh_vien', 'thu']]
        ordering = ['benh_vien', 'thu']
        verbose_name = 'Giờ làm việc bệnh viện'
        verbose_name_plural = 'Giờ làm việc bệnh viện'

    def __str__(self):
        return f"{self.benh_vien.ten} - {self.get_thu_display()}"


# ========================= 
# KHOA
# ========================= 
class Khoa(models.Model):
    ten = models.CharField(max_length=200, db_index=True)
    benh_vien = models.ForeignKey(
        BenhVien,
        on_delete=models.CASCADE,
        related_name='khoas',
        db_index=True
    )

    class Meta:
        unique_together = [['ten', 'benh_vien']]
        verbose_name = 'Khoa'
        verbose_name_plural = 'Khoa'

    def __str__(self):
        return f"{self.ten} - {self.benh_vien.ten}"


# ========================= 
# BÁC SĨ
# ========================= 
class BacSi(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='bac_si',
        null=True,
        blank=True
    )
    ho_ten = models.CharField(max_length=255, db_index=True)
    chuyen_khoa = models.CharField(max_length=200, db_index=True)
    khoa = models.ForeignKey(
        Khoa,
        on_delete=models.CASCADE,
        related_name='bac_sis'
    )
    benh_vien = models.ForeignKey(
        BenhVien,
        on_delete=models.CASCADE,
        related_name='bac_sis'
    )
    so_dien_thoai = models.CharField(max_length=15)

    class Meta:
        indexes = [
            models.Index(fields=['benh_vien', 'chuyen_khoa']),
        ]
        verbose_name = 'Bác sĩ'
        verbose_name_plural = 'Bác sĩ'

    def __str__(self):
        return self.ho_ten


# ========================= 
# GIỜ LÀM VIỆC BÁC SĨ
# ========================= 
class GioLamViecBacSi(models.Model):
    bac_si = models.ForeignKey(
        BacSi,
        on_delete=models.CASCADE,
        related_name='gio_lam_viecs'
    )
    thu = models.IntegerField(
        choices=[
            (0, 'Chủ nhật'),
            (1, 'Thứ 2'),
            (2, 'Thứ 3'),
            (3, 'Thứ 4'),
            (4, 'Thứ 5'),
            (5, 'Thứ 6'),
            (6, 'Thứ 7'),
        ],
        db_index=True
    )
    gio_bat_dau = models.TimeField()
    gio_ket_thuc = models.TimeField()
    nghi = models.BooleanField(default=False)

    class Meta:
        unique_together = [['bac_si', 'thu']]
        ordering = ['bac_si', 'thu']
        verbose_name = 'Giờ làm việc bác sĩ'
        verbose_name_plural = 'Giờ làm việc bác sĩ'

    def __str__(self):
        return f"{self.bac_si.ho_ten} - {self.get_thu_display()}"


# ========================= 
# BẢO HIỂM Y TẾ
# ========================= 
class BaoHiemYTe(models.Model):
    ma_bhyt = models.CharField(max_length=50, unique=True)
    ngay_cap = models.DateField()
    ngay_het_han = models.DateField(db_index=True)

    class Meta:
        verbose_name = 'Bảo hiểm y tế'
        verbose_name_plural = 'Bảo hiểm y tế'

    def __str__(self):
        return self.ma_bhyt


# ========================= 
# BỆNH NHÂN
# ========================= 
class BenhNhan(models.Model):
    ho_ten = models.CharField(max_length=255, db_index=True)
    ngay_sinh = models.DateField()
    gioi_tinh = models.CharField(
        max_length=10,
        choices=[
            ('nam', 'Nam'),
            ('nu', 'Nữ'),
            ('khac', 'Khác')
        ]
    )
    so_dien_thoai = models.CharField(max_length=15, db_index=True)
    dia_chi = models.TextField()
    bhyt = models.OneToOneField(
        BaoHiemYTe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='benh_nhan'
    )

    class Meta:
        verbose_name = 'Bệnh nhân'
        verbose_name_plural = 'Bệnh nhân'

    def __str__(self):
        return self.ho_ten


# ========================= 
# LỊCH KHÁM
# ========================= 
class LichKham(models.Model):
    benh_nhan = models.ForeignKey(
        BenhNhan,
        on_delete=models.CASCADE,
        related_name='lich_khams'
    )
    bac_si = models.ForeignKey(
        BacSi,
        on_delete=models.CASCADE,
        related_name='lich_khams'
    )
    ngay_kham = models.DateField(db_index=True)
    gio_kham = models.TimeField()
    trang_thai = models.CharField(
        max_length=20,
        choices=[
            ('cho', 'Chờ khám'),
            ('dang', 'Đang khám'),
            ('xong', 'Đã xong'),
            ('huy', 'Đã hủy')
        ],
        default='cho',
        db_index=True
    )
    ghi_chu = models.TextField(blank=True, default='')
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['bac_si', 'ngay_kham', 'trang_thai']),
            models.Index(fields=['benh_nhan', 'ngay_kham']),
        ]
        unique_together = [['bac_si', 'ngay_kham', 'gio_kham']]
        ordering = ['-ngay_kham', '-gio_kham']
        verbose_name = 'Lịch khám'
        verbose_name_plural = 'Lịch khám'

    def __str__(self):
        return f"{self.benh_nhan.ho_ten} - {self.ngay_kham}"


# ========================= 
# PHIẾU KHÁM
# ========================= 
class PhieuKham(models.Model):
    benh_nhan = models.ForeignKey(
        BenhNhan,
        on_delete=models.CASCADE,
        related_name='phieu_khams'
    )
    lich_kham = models.OneToOneField(
        LichKham,
        on_delete=models.CASCADE,
        related_name='phieu_kham'
    )
    trieu_chung = models.TextField()
    chan_doan = models.TextField()
    huong_dieu_tri = models.TextField()
    ngay_lap = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-ngay_lap']
        verbose_name = 'Phiếu khám'
        verbose_name_plural = 'Phiếu khám'

    def __str__(self):
        return f"Phiếu {self.benh_nhan.ho_ten} - {self.ngay_lap.date()}"


# ========================= 
# LỊCH SỬ KHÁM BỆNH
# ========================= 
class LichSuKhamBenh(models.Model):
    benh_nhan = models.ForeignKey(
        BenhNhan,
        on_delete=models.CASCADE,
        related_name='lich_su_khams',
        db_index=True
    )
    bac_si = models.ForeignKey(
        BacSi,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lich_su_khams'
    )
    benh_vien = models.ForeignKey(
        BenhVien,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lich_su_khams'
    )
    phieu_kham = models.ForeignKey(
        PhieuKham,
        on_delete=models.CASCADE,
        related_name='lich_sus',
        null=True,
        blank=True
    )
    ngay_kham = models.DateField(db_index=True)
    trieu_chung = models.TextField()
    chan_doan = models.TextField()
    huong_dieu_tri = models.TextField()
    ghi_chu = models.TextField(blank=True, default='')
    ngay_tao = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['benh_nhan', '-ngay_kham']),
            models.Index(fields=['bac_si', '-ngay_kham']),
            models.Index(fields=['benh_vien', '-ngay_kham']),
        ]
        ordering = ['-ngay_kham', '-ngay_tao']
        verbose_name = 'Lịch sử khám bệnh'
        verbose_name_plural = 'Lịch sử khám bệnh'

    def __str__(self):
        return f"{self.benh_nhan.ho_ten} - {self.ngay_kham}"


# ========================= 
# LOG LỊCH KHÁM
# ========================= 
class LogLichKham(models.Model):
    lich_kham = models.ForeignKey(
        LichKham,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    hanh_dong = models.CharField(
        max_length=50,
        choices=[
            ('tao_moi', 'Tạo mới'),
            ('cap_nhat', 'Cập nhật'),
            ('doi_trang_thai', 'Đổi trạng thái'),
            ('huy', 'Hủy lịch'),
            ('hoan_thanh', 'Hoàn thành'),
        ],
        db_index=True
    )
    trang_thai_cu = models.CharField(max_length=20, blank=True, default='')
    trang_thai_moi = models.CharField(max_length=20, blank=True, default='')
    nguoi_thuc_hien = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='log_lich_khams'
    )
    mo_ta = models.TextField(blank=True, default='')
    thoi_gian = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['lich_kham', '-thoi_gian']),
            models.Index(fields=['nguoi_thuc_hien', '-thoi_gian']),
            models.Index(fields=['hanh_dong', '-thoi_gian']),
        ]
        ordering = ['-thoi_gian']
        verbose_name = 'Log lịch khám'
        verbose_name_plural = 'Log lịch khám'

    def __str__(self):
        return f"{self.get_hanh_dong_display()} - {self.thoi_gian}"


# ========================= 
# LOG HỆ THỐNG
# ========================= 
class LogHeThong(models.Model):
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.IntegerField(db_index=True)
    hanh_dong = models.CharField(
        max_length=50,
        choices=[
            ('create', 'Tạo mới'),
            ('update', 'Cập nhật'),
            ('delete', 'Xóa'),
        ],
        db_index=True
    )
    du_lieu_cu = models.JSONField(null=True, blank=True)
    du_lieu_moi = models.JSONField(null=True, blank=True)
    nguoi_thuc_hien = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='log_he_thongs'
    )
    thoi_gian = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ghi_chu = models.TextField(blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['model_name', 'object_id', '-thoi_gian']),
            models.Index(fields=['nguoi_thuc_hien', '-thoi_gian']),
            models.Index(fields=['hanh_dong', '-thoi_gian']),
        ]
        ordering = ['-thoi_gian']
        verbose_name = 'Log hệ thống'
        verbose_name_plural = 'Log hệ thống'

    def __str__(self):
        return f"{self.model_name} - {self.get_hanh_dong_display()} - {self.thoi_gian}"


# ========================= 
# THÔNG BÁO
# ========================= 
class ThongBao(models.Model):
    nguoi_nhan = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='thong_baos',
    null=True,
    blank=True
    )
    loai = models.CharField(
        max_length=50,
        choices=[
            ('lich_kham', 'Lịch khám'),
            ('phieu_kham', 'Phiếu khám'),
            ('he_thong', 'Hệ thống'),
            ('nhac_nho', 'Nhắc nhở'),
        ],
        default='he_thong',
        db_index=True
    )
    tieu_de = models.CharField(max_length=255)
    noi_dung = models.TextField()
    lien_ket = models.CharField(max_length=500, blank=True, default='')
    thoi_gian = models.DateTimeField(auto_now_add=True, db_index=True)
    da_doc = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['nguoi_nhan', 'da_doc', '-thoi_gian']),
            models.Index(fields=['loai', '-thoi_gian']),
        ]
        ordering = ['-thoi_gian']
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'

    def __str__(self):
        return self.tieu_de


# ========================= 
# SIGNALS - AUTO LOG
# ========================= 

# Auto log khi tạo lịch sử khám bệnh từ phiếu khám
@receiver(post_save, sender=PhieuKham)
def tao_lich_su_kham_benh(sender, instance, created, **kwargs):
    """Tự động tạo lịch sử khám bệnh khi có phiếu khám mới"""
    if created:
        LichSuKhamBenh.objects.create(
            benh_nhan=instance.benh_nhan,
            bac_si=instance.lich_kham.bac_si,
            benh_vien=instance.lich_kham.bac_si.benh_vien,
            phieu_kham=instance,
            ngay_kham=instance.lich_kham.ngay_kham,
            trieu_chung=instance.trieu_chung,
            chan_doan=instance.chan_doan,
            huong_dieu_tri=instance.huong_dieu_tri,
            ghi_chu=instance.lich_kham.ghi_chu
        )


# Auto log khi tạo lịch khám mới
@receiver(post_save, sender=LichKham)
def log_tao_lich_kham(sender, instance, created, **kwargs):
    """Tự động log khi tạo lịch khám mới"""
    if created:
        LogLichKham.objects.create(
            lich_kham=instance,
            hanh_dong='tao_moi',
            trang_thai_moi=instance.trang_thai,
            mo_ta=f"Tạo lịch khám mới cho bệnh nhân {instance.benh_nhan.ho_ten}"
        )


# Auto log khi thay đổi trạng thái lịch khám
@receiver(pre_save, sender=LichKham)
def log_thay_doi_trang_thai(sender, instance, **kwargs):
    """Tự động log khi thay đổi trạng thái lịch khám"""
    if instance.pk:
        try:
            old_instance = LichKham.objects.get(pk=instance.pk)
            if old_instance.trang_thai != instance.trang_thai:
                LogLichKham.objects.create(
                    lich_kham=instance,
                    hanh_dong='doi_trang_thai',
                    trang_thai_cu=old_instance.trang_thai,
                    trang_thai_moi=instance.trang_thai,
                    mo_ta=f"Đổi trạng thái từ {old_instance.get_trang_thai_display()} sang {instance.get_trang_thai_display()}"
                )
        except LichKham.DoesNotExist:
            pass


# Auto tạo thông báo khi có lịch khám mới
@receiver(post_save, sender=LichKham)
def tao_thong_bao_lich_kham(sender, instance, created, **kwargs):
    """Tự động tạo thông báo cho bác sĩ khi có lịch khám mới"""
    if created and instance.bac_si.user:
        ThongBao.objects.create(
            nguoi_nhan=instance.bac_si.user,
            loai='lich_kham',
            tieu_de='Lịch khám mới',
            noi_dung=f"Bệnh nhân {instance.benh_nhan.ho_ten} đã đặt lịch khám vào {instance.ngay_kham} lúc {instance.gio_kham}",
            lien_ket=f"/lich-kham/{instance.pk}/"
        )


# Auto tạo thông báo khi có phiếu khám mới
@receiver(post_save, sender=PhieuKham)
def tao_thong_bao_phieu_kham(sender, instance, created, **kwargs):
    """Tự động tạo thông báo khi có phiếu khám hoàn thành"""
    if created:
        ThongBao.objects.create(
            nguoi_nhan=instance.lich_kham.bac_si.user if instance.lich_kham.bac_si.user else None,
            loai='phieu_kham',
            tieu_de='Phiếu khám mới',
            noi_dung=f"Đã hoàn thành phiếu khám cho bệnh nhân {instance.benh_nhan.ho_ten}",
            lien_ket=f"/phieu-kham/{instance.pk}/"
        )