"""Explicit developer setup and source distribution build for PresentMon 2.3.1."""
import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile, ZIP_DEFLATED
from version import __version__

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
EXE_NAME = "PresentMon-2.3.1-x64.exe"
EXE = TOOLS / EXE_NAME
NOTICE = TOOLS / "PresentMon-README.md"
SHA256 = "364e5d98d4d134bd54dd25c22ed2ca2f4883f8bc3ed6502bee0c151e3436d30c"
URL = "https://github.com/GameTechDev/PresentMon/releases/download/v2.3.1/" + EXE_NAME
NOTICE_URL = "https://raw.githubusercontent.com/GameTechDev/PresentMon/v2.3.1/README.md"

RUNTIME_FILES = (
    "main.py", "qt_gui.py", "qt_theme.py", "qt_pages.py", "qt_monitor.py",
    "qt_gaming.py", "gaming_metrics.py", "qt_fps.py", "process_picker.py", "qt_dialogs.py",
    "preferences.py", "qt_settings.py",
    "presentmon_capture.py", "presentmon_bundle.py", "presentmon_errors.py", "frame_metrics.py",
    "hardware_metrics.py", "process_metrics.py", "performance_logger.py",
    "performance_analysis.py", "version.py", "requirements.txt", "README.md",
    "CHANGELOG.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
)


def verified_binary(path=EXE):
    try:
        with Path(path).open("rb") as file:
            return hashlib.file_digest(file, "sha256").hexdigest() == SHA256
    except OSError:
        return False


def bundled_exe():
    return EXE if verified_binary() and NOTICE.is_file() else None


def download(url, limit):
    with urlopen(url, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Unexpected download size")
    return data


def prepare():
    TOOLS.mkdir(exist_ok=True)
    if not verified_binary():
        binary = download(URL, 5_000_000)
        if hashlib.sha256(binary).hexdigest() != SHA256:
            raise ValueError("PresentMon SHA-256 mismatch; executable was not installed.")
        temp = EXE.with_suffix(".tmp")
        try:
            temp.write_bytes(binary)
            temp.replace(EXE)
        finally:
            temp.unlink(missing_ok=True)
    if not NOTICE.is_file():
        notice = download(NOTICE_URL, 1_000_000)
        if b"Permission is hereby granted" not in notice or b"Copyright" not in notice:
            raise ValueError("Upstream license notice could not be verified.")
        NOTICE.write_bytes(notice)
    print("PresentMon verified:", EXE)


def package():
    prepare()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    destination = dist / f"PC-Monitor-v{__version__}-source-windows-x64.zip"
    temp = destination.with_suffix(".tmp")
    try:
        with ZipFile(temp, "w", ZIP_DEFLATED) as archive:
            for name in RUNTIME_FILES:
                archive.write(ROOT / name, name)
            archive.write(EXE, "tools/" + EXE_NAME)
            archive.write(NOTICE, "tools/" + NOTICE.name)
        temp.replace(destination)
    finally:
        temp.unlink(missing_ok=True)
    print("Distribution:", destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true", help="Build source ZIP including PresentMon")
    args = parser.parse_args()
    try:
        package() if args.package else prepare()
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Setup failed: {exc}\n")


if __name__ == "__main__":
    main()
