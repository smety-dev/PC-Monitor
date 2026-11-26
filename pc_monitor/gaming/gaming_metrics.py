"""Pure helpers for the gaming overlay; no GUI or system calls."""
import math

CORNERS = ("Vlevo nahoře", "Vpravo nahoře", "Vlevo dole", "Vpravo dole")


def finite(value):
    return value is not None and math.isfinite(value) and value >= 0


def percent(value):
    return f"{value:.0f} %" if finite(value) else "N/A"


def fraction(value):
    return min(1.0, value / 100) if finite(value) else 0.0


def frequency(value):
    return f"{value / 1000:.2f} GHz" if finite(value) else "N/A"


def available_memory(value):
    return f"{value / 1024**3:.1f} GiB volné" if finite(value) else "N/A"


def overlay_position(rect, size, corner, margin=16):
    """Place in a screen rectangle (including negative monitor coordinates)."""
    x, y, width, height = rect
    w, h = size
    if corner not in CORNERS:
        raise ValueError("Unknown corner")
    inset_x = min(margin, max(0, (width - w) // 2))
    inset_y = min(margin, max(0, (height - h) // 2))
    left = x + inset_x
    right = x + max(0, width - w - inset_x)
    top = y + inset_y
    bottom = y + max(0, height - h - inset_y)
    return (right if corner.startswith("Vpravo") else left,
            bottom if corner.endswith("dole") else top)
