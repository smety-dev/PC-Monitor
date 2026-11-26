import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import presentmon_bundle as bundle
from presentmon_errors import capture_error


class PresentMonBundleTests(unittest.TestCase):
    def test_verified_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.exe"
            path.write_bytes(b"test")
            with patch.object(bundle, "SHA256", hashlib.sha256(b"test").hexdigest()):
                self.assertTrue(bundle.verified_binary(path))
                path.write_bytes(b"changed")
                self.assertFalse(bundle.verified_binary(path))
                self.assertFalse(bundle.verified_binary(path.with_suffix(".missing")))

    def test_runtime_manifest(self):
        for name in bundle.RUNTIME_FILES:
            self.assertTrue((bundle.ROOT / name).is_file(), name)
        self.assertIn("presentmon_errors.py", bundle.RUNTIME_FILES)
        self.assertIn("THIRD_PARTY_NOTICES.md", bundle.RUNTIME_FILES)

    def test_access_denied(self):
        message = capture_error(6, "failed to start trace session: access denied.")
        self.assertIn("Performance Log Users", message)
        self.assertIn("IT", message)

    def test_other_error_not_mislabeled(self):
        self.assertIn("kód 6", capture_error(6, "unrelated error"))
        self.assertNotIn("oprávnění", capture_error(6, "unrelated error"))
        self.assertIn("skončilo", capture_error(0, ""))
