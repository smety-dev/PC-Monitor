import unittest
from pc_monitor.locales.i18n import resolve_language, set_language, tr, decimal


class LanguageTests(unittest.TestCase):
    def tearDown(self):
        set_language("cs")

    def test_system_fallback_and_explicit_choice(self):
        self.assertEqual(resolve_language("auto", "cs_CZ"), "cs")
        self.assertEqual(resolve_language("auto", "de_DE"), "en")
        self.assertEqual(resolve_language("auto", "en_US"), "en")
        self.assertEqual(resolve_language("en", "cs_CZ"), "en")
        self.assertEqual(resolve_language("cs", "en_US"), "cs")

    def test_translation_and_dynamic_values(self):
        set_language("en")
        self.assertEqual(tr("Přehled"), "Overview")
        self.assertEqual(tr("6 jader / 12 vláken"), "6 cores / 12 threads")
        self.assertEqual(tr("2.6 GiB volných z 15.7 GiB"), "2.6 GiB free of 15.7 GiB")
        self.assertEqual(tr("PresentMon skončil (kód 6). detail"), "PresentMon exited (code 6). detail")
        self.assertEqual(tr("CPU celkem: nejméně polovina dostupných vzorků dosahuje 90 %."), "Total CPU: at least half of available samples reach 90 %.")
        self.assertEqual(tr("arbitrary diagnostic"), "arbitrary diagnostic")
        self.assertEqual(decimal("12.5"), "12.5")
        set_language("cs")
        self.assertEqual(tr("Přehled"), "Přehled")
        self.assertEqual(decimal("12.5"), "12,5")
