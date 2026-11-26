"""Local user preferences; runtime sessions and process IDs are never persisted."""
from gaming_metrics import CORNERS

PAGES = ("Přehled", "Procesor", "Disky", "Síť", "Procesy", "Záznam", "Analýza", "Gaming", "Benchmark", "Nastavení")
DEFAULTS = {
    "startup/remember_page": True,
    "startup/remember_geometry": True,
    "startup/last_page": "Přehled",
    "overlay/monitor": "",
    "overlay/corner": CORNERS[1],
    "overlay/opacity": 90,
    "overlay/details": True,
    "overlay/fps": True,
    "gaming/low_overhead": True,
    "recording/interval": 1,
}
GEOMETRY_KEY = "window/geometry"


def normalize(key, value):
    """Reject invalid or obsolete values without breaking application startup."""
    default = DEFAULTS[key]
    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
        if str(value).lower() in ("true", "1"):
            return True
        if str(value).lower() in ("false", "0"):
            return False
        return default
    if isinstance(default, int):
        try:
            number = int(str(value))
        except (TypeError, ValueError):
            return default
        if key == "overlay/opacity":
            return min(100, max(35, number))
        return number if number in (1, 2, 5, 10) else default
    if key == "overlay/corner":
        return value if isinstance(value, str) and value in CORNERS else default
    if key == "startup/last_page":
        return value if isinstance(value, str) and value in PAGES else default
    return value if isinstance(value, str) else default


class Preferences:
    def __init__(self, store=None):
        if store is None:
            from PySide6.QtCore import QSettings
            store = QSettings("smety-dev", "PC Monitor")
            store.setFallbacksEnabled(False)
        self.store = store

    def get(self, key):
        return normalize(key, self.store.value(key, DEFAULTS[key]))

    def set(self, key, value):
        self.store.setValue(key, normalize(key, value))

    def geometry(self):
        return self.store.value(GEOMETRY_KEY)

    def save_geometry(self, value):
        self.store.setValue(GEOMETRY_KEY, value)

    def remove_geometry(self):
        self.store.remove(GEOMETRY_KEY)

    def reset(self):
        for key in (*DEFAULTS, GEOMETRY_KEY):
            self.store.remove(key)
        self.sync()

    def sync(self):
        self.store.sync()
