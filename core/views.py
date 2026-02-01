from django.shortcuts import render, get_object_or_404
from .models import BenhVien


def home(request):
    bvs = BenhVien.objects.all()
    return render(request, "core/home.html", {
        "bvs": bvs
    })

def hospital_detail(request, id):
    bv = get_object_or_404(BenhVien, id=id)

    khoas = bv.khoas.all()
    bac_sis = bv.bac_sis.all()

    return render(request, "core/hospital_detail.html", {
        "bv": bv,
        "khoas": khoas,
        "bac_sis": bac_sis,
    })