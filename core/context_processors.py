from .models import ThongBao

def unread_notifications(request):
    if request.user.is_authenticated:
        unread_count = ThongBao.objects.filter(
            nguoi_nhan=request.user,
            da_doc=False,
        ).count()
        return {'unread_count': unread_count}
    return {'unread_count': 0}
