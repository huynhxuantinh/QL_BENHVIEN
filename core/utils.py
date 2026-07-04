import math

def mercator_to_wgs84(x, y):
    """
    Convert Web Mercator coordinates (EPSG:3857) to WGS84 (EPSG:4326).
    Returns (lon, lat) tuple.
    """
    max_merc = 20037508.34
    world_width = max_merc * 2
    
    if x > max_merc or x < -max_merc:
        x = ((x + max_merc) % world_width) - max_merc
    if y > max_merc:
        y = max_merc
    elif y < -max_merc:
        y = -max_merc
        
    lon = x * 180.0 / 20037508.34
    lat = y * 180.0 / 20037508.34
    lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2)
    
    return lon, lat

def point_to_latlon(point):
    """
    GIS: convert Point to lat/lon (handle Web Mercator or WGS84)
    Returns (lat, lon) or (None, None).
    """
    if not point:
        return None, None
    x = point.x
    y = point.y
    is_web_mercator = getattr(point, "srid", None) == 3857 or abs(x) > 180 or abs(y) > 90
    if is_web_mercator:
        lon, lat = mercator_to_wgs84(x, y)
        if abs(lat) <= 90 and abs(lon) <= 180:
            return lat, lon
        if abs(y) <= 90 and abs(x) <= 180:
            return y, x
        return None, None
    return y, x

def _translate_password_validation_message(message):
    mapping = {
        "This password is too short. It must contain at least 8 characters.": "Mật khẩu quá ngắn. Mật khẩu phải có ít nhất 8 ký tự.",
        "This password is too common.": "Mật khẩu quá phổ biến, vui lòng chọn mật khẩu khác an toàn hơn.",
        "This password is entirely numeric.": "Mật khẩu không được chỉ gồm chữ số.",
        "The password is too similar to the username.": "Mật khẩu quá giống với tên người dùng.",
    }
    return mapping.get(message, message)

def get_client_ip(request):
    """
    Get the real client IP address, handling reverse proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')
