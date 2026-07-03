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
