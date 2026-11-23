"""Physical constraints for publication exports."""

import math


A4_CONTENT_HEIGHT_INCHES = 267 / 25.4
RASTER_MAX_DIMENSION = 32000
RASTER_MAX_PIXELS = 150_000_000


def raster_dpi_limit(width: float, height: float, maximum: int) -> int:
    dpi = min(maximum, math.floor(min(
        RASTER_MAX_DIMENSION / max(width, height),
        math.sqrt(RASTER_MAX_PIXELS / (width * height)),
    )))
    while dpi > 0:
        pixels_w, pixels_h = math.ceil(width * dpi), math.ceil(height * dpi)
        if max(pixels_w, pixels_h) <= RASTER_MAX_DIMENSION and pixels_w * pixels_h <= RASTER_MAX_PIXELS:
            break
        dpi -= 1
    return dpi
