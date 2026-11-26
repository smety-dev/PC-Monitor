"""Ensure release metadata stays in sync."""
import re
import unittest
from pathlib import Path
from pc_monitor.version import __version__

ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_readme_version(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(re.search(r"Current version: v([\d.]+)", text).group(1), __version__)

    def test_website_version(self):
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(re.search(r'name="pc-monitor-version" content="([\d.]+)"', html).group(1), __version__)

    def test_english_dashboard_preview(self):
        import xml.etree.ElementTree as ET
        svg = ET.parse(ROOT / "docs" / "assets" / "dashboard-demo.svg")
        text = {element.text for element in svg.iter()
                if element.tag.endswith("}text")}
        self.assertIn("VERSION " + __version__, text)
        self.assertIn("System overview", text)
        self.assertIn("Network activity", text)
        self.assertNotIn("Přehled systému", text)
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn("assets/dashboard-demo.svg", html)
        self.assertIn("All values are simulated", html)

    def test_latest_changelog_version(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(re.search(r"^## \[([\d.]+)\]", text, re.MULTILINE).group(1), __version__)
