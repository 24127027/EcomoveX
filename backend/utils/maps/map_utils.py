import math


async def interpolate_search_params(distance: float) -> tuple[int, float]:
    r_min, r_max = 300, 5000
    d_max = 500000
    alpha = 1.2
    distance = max(0.0, distance)

    if distance < 100:
        radius = 100
    else:
        ratio = math.log10(min(distance, d_max) + 1) / math.log10(d_max + 1)
        radius = r_min + (r_max - r_min) * ratio

    if distance > d_max:
        radius += 1000 * math.log10(distance / d_max + 1)

    interval = radius * alpha
    return int(radius), interval
