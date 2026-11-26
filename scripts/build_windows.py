"""Create and smoke-test a portable Windows x64 distribution, then zip it."""
import hashlib
import importlib.metadata as metadata
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from pc_monitor.gaming.presentmon_bundle import prepare, EXE, NOTICE, verified_binary
from pc_monitor.version import __version__

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WORK = ROOT / "build" / "windows"
APP = DIST / "PC-Monitor"


def run(*args, **kwargs):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True, **kwargs)


def collect_notices():
    """Preserve installed wheel notices and record the exact build environment."""
    folder = APP / "licenses"
    folder.mkdir()
    manifest = []
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata.get("Name", "").lower()):
        name = dist.metadata.get("Name", "unknown")
        manifest.append(f"{name}=={dist.version}")
        for entry in dist.files or ():
            parts = [p.lower() for p in entry.parts]
            filename = entry.name.lower()
            if not ("licenses" in parts or filename.startswith(("license", "licence", "copying", "notice", "copyright"))):
                continue
            source = Path(dist.locate_file(entry))
            if not source.is_file():
                continue
            if any(part in ("..", "") for part in entry.parts):
                continue
            target = folder / name / entry
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for candidate in (Path(sys.base_prefix) / "LICENSE.txt", Path(sys.base_prefix) / "LICENSE"):
        if candidate.is_file():
            shutil.copy2(candidate, folder / "Python-LICENSE.txt")
            break
    (APP / "build-dependencies.txt").write_text("Python " + platform.python_version() + "\n" +
                                               "\n".join(manifest) + "\n", encoding="utf-8")


def build():
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64") or sys.maxsize <= 2**32:
        raise SystemExit("Build requires Windows x64 and 64-bit Python.")
    if sys.prefix == sys.base_prefix:
        raise SystemExit("Use a clean virtual environment, not global Python.")
    prepare()
    WORK.mkdir(parents=True, exist_ok=True)
    from PySide6.QtWidgets import QApplication
    from pc_monitor.ui.app_identity import write_ico
    app = QApplication([])
    icon = WORK / "PC-Monitor.ico"
    write_ico(icon)
    app.quit()
    version = tuple(int(n) for n in __version__.split(".")) + (0,)
    resource = WORK / "version.txt"
    resource.write_text(
        f"VSVersionInfo(ffi=FixedFileInfo(filevers={version}, prodvers={version}, mask=0x3f, "
        "flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)), kids=["
        "StringFileInfo([StringTable('040904B0', ["
        "StringStruct('FileDescription', 'PC Monitor'),"
        f"StringStruct('FileVersion', '{__version__}'),"
        "StringStruct('ProductName', 'PC Monitor'),"
        f"StringStruct('ProductVersion', '{__version__}'),"
        "StringStruct('OriginalFilename', 'PC-Monitor.exe')])]),"
        "VarFileInfo([VarStruct('Translation', [1033, 1200])])])",
        encoding="utf-8")
    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--windowed", "--noupx", "--name", "PC-Monitor", "--icon", icon,
        "--version-file", resource, "--distpath", DIST, "--workpath", WORK / "pyinstaller",
        "--specpath", WORK, "--exclude-module", "tkinter", "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6", "--exclude-module", "PySide2", ROOT / "main.py")
    tools = APP / "tools"
    tools.mkdir()
    shutil.copy2(EXE, tools / EXE.name)
    shutil.copy2(NOTICE, tools / NOTICE.name)
    if not verified_binary(tools / EXE.name):
        raise RuntimeError("Packaged PresentMon hash mismatch")
    for name in ("README.md", "LICENSE", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md", "RELEASE_NOTES.md", "GUIDE.md", "ROADMAP.md"):
        shutil.copy2(ROOT / name, APP / name)
    shutil.copytree(ROOT / "docs" / "assets", APP / "docs" / "assets")
    collect_notices()

    marker = WORK / "smoke.txt"
    for path in (marker, marker.with_suffix(".ini"), marker.with_suffix(".png")):
        path.unlink(missing_ok=True)
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    run(APP / "PC-Monitor.exe", "--smoke-test", marker, env=env, timeout=90)
    if not marker.is_file() or marker.read_text(encoding="utf-8") != "OK " + __version__:
        raise RuntimeError("Packaged application smoke test did not complete")
    filename = f"PC-Monitor-v{__version__}-Windows-x64.zip"
    archive = DIST / filename
    temp = archive.with_suffix(".tmp")
    try:
        with ZipFile(temp, "w", ZIP_DEFLATED, compresslevel=6) as z:
            for path in sorted(APP.rglob("*")):
                if path.is_file():
                    z.write(path, path.relative_to(DIST))
        temp.replace(archive)
    finally:
        temp.unlink(missing_ok=True)
    with archive.open("rb") as file:
        digest = hashlib.file_digest(file, "sha256").hexdigest()
    (DIST / (filename + ".sha256")).write_text(f"{digest}  {filename}\n", encoding="ascii")
    print("Portable package:", archive)


if __name__ == "__main__":
    build()
