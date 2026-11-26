"""Preference tests do not modify the user's real Qt settings."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_monitor.core.preferences import DEFAULTS, GEOMETRY_KEY, Preferences, normalize


class MemoryStore:
    def __init__(self):
        self.data = {}

    def value(self, key, default=None):
        return self.data.get(key, default)

    def setValue(self, key, value):
        self.data[key] = value

    def remove(self, key):
        self.data.pop(key, None)

    def sync(self):
        pass


class PreferencesTests(unittest.TestCase):
    def test_defaults(self):
        prefs = Preferences(MemoryStore())
        for key, default in DEFAULTS.items():
            self.assertEqual(prefs.get(key), default)

    def test_boolean_values(self):
        for value in (True, "true", "1"):
            self.assertIs(normalize("overlay/fps", value), True)
        for value in (False, "false", "0"):
            self.assertIs(normalize("overlay/fps", value), False)
        self.assertIs(normalize("overlay/fps", "invalid"), True)

    def test_numeric_values(self):
        self.assertEqual(normalize("overlay/opacity", 10), 35)
        self.assertEqual(normalize("overlay/opacity", "150"), 100)
        self.assertEqual(normalize("overlay/opacity", "invalid"), 90)
        self.assertEqual(normalize("recording/interval", "5"), 5)
        self.assertEqual(normalize("recording/interval", 3), 1)

    def test_invalid_choices(self):
        self.assertEqual(normalize("overlay/corner", "invalid"), DEFAULTS["overlay/corner"])
        self.assertEqual(normalize("startup/last_page", "old"), "Přehled")
        self.assertEqual(normalize("startup/last_page", "Gaming"), "Gaming")
        self.assertEqual(normalize("overlay/monitor", None), "")

    def test_language_preference(self):
        store = MemoryStore()
        prefs = Preferences(store)
        self.assertEqual(prefs.get("ui/language"), "auto")
        prefs.set("ui/language", "en")
        self.assertEqual(Preferences(store).get("ui/language"), "en")
        prefs.set("ui/language", "invalid")
        self.assertEqual(prefs.get("ui/language"), "auto")

    def test_storage_roundtrip(self):
        store = MemoryStore()
        prefs = Preferences(store)
        prefs.set("overlay/opacity", 55)
        prefs.set("gaming/low_overhead", False)
        prefs.set("overlay/monitor", "DISPLAY2")
        prefs.save_geometry(b"geometry")
        restored = Preferences(store)
        self.assertEqual(restored.get("overlay/opacity"), 55)
        self.assertFalse(restored.get("gaming/low_overhead"))
        self.assertEqual(restored.get("overlay/monitor"), "DISPLAY2")
        self.assertEqual(restored.geometry(), b"geometry")

    def test_reset_only_owned_keys(self):
        store = MemoryStore()
        prefs = Preferences(store)
        store.setValue("unrelated/key", "keep")
        for key, default in DEFAULTS.items():
            prefs.set(key, default)
        prefs.save_geometry(b"geometry")
        prefs.reset()
        self.assertEqual(store.data, {"unrelated/key": "keep"})
        self.assertIsNone(prefs.geometry())

    def test_real_qsettings_ini_roundtrip(self):
        from PySide6.QtCore import QByteArray, QSettings
        with TemporaryDirectory() as folder:
            path = str(Path(folder) / "test.ini")
            prefs = Preferences(QSettings(path, QSettings.Format.IniFormat))
            prefs.set("overlay/opacity", 60)
            prefs.set("startup/remember_page", False)
            prefs.save_geometry(QByteArray(b"geometry"))
            prefs.sync()
            restored = Preferences(QSettings(path, QSettings.Format.IniFormat))
            self.assertEqual(restored.get("overlay/opacity"), 60)
            self.assertFalse(restored.get("startup/remember_page"))
            self.assertEqual(bytes(restored.geometry()), b"geometry")
            restored.remove_geometry()
            restored.sync()
            self.assertIsNone(restored.geometry())
            del prefs, restored
