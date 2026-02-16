from django import forms
from .models import LichKham, BacSi


class DatLichForm(forms.ModelForm):
    class Meta:
        model = LichKham
        fields = ['bac_si', 'ngay_kham', 'gio_kham', 'ghi_chu']

        widgets = {
            'ngay_kham': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'gio_kham': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'step': '1800',
                'min': '00:00',
                'max': '23:30',
            }),
            'ghi_chu': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
        }

    bac_si = forms.ModelChoiceField(
        queryset=BacSi.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
