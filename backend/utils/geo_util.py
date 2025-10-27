import hashlib

def stable_location_id(lat: float, lon: float) -> str:
    s = f"{round(lat, 6)}:{round(lon, 6)}"
    return hashlib.md5(s.encode()).hexdigest()