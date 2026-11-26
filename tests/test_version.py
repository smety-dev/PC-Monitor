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

    def test_latest_changelog_version(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(re.search(r"^## \[([\d.]+)\]", text, re.MULTILINE).group(1), __version__)
