from .models import ThongBao

def unread_notifications(request):
    if request.user.is_authenticated and \
       not request.user.is_superuser and \
       not request.user.is_staff and \
       not hasattr(request.user, 'bac_si'):
        count = ThongBao.objects.filter(
            nguoi_nhan=request.user, da_doc=False
        ).count()
        return {'unread_count': count}
    return {'unread_count': 0}
