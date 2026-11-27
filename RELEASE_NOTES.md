# PC Monitor v0.9.7 — GPU Compatibility Hotfix candidate

## What's fixed
- Windows PowerShell module discovery when launched from PowerShell 7 or VS Code.
- GPU 3D measurement with a locale-independent WMI fallback on errors or repeated missing samples.
- GPU provider error logging without inventing utilization values.
- The original fix was reported working on an RX 6600 XT in PR #19; final hotfix hardware and EXE validation is pending.

## Run on Windows x64
Extract the entire archive to a local writable directory and open **PC-Monitor.exe**.
Keep the `_internal` and `tools` folders beside the executable. No Python installation is required.
The application is unsigned; Windows SmartScreen may display a warning. Only download from the official repository and verify the published SHA-256.

## Features
- CPU, RAM, GPU 3D, storage, network and process monitoring.
- Live charts, local CSV recording and offline analysis.
- Gaming overlay, PresentMon FPS and timed A/B benchmarks.
- Persistent local preferences and Czech/English language selection. Settings apply after restarting the application; the default follows the system language (Czech or English fallback).

## Known limitations
- Native file dialogs and raw system/PresentMon diagnostics may retain their original language. CSV headers and numeric formats remain compatible with v0.9.6.
- Beta software. Actual game FPS capture and clean-machine compatibility require manual validation.
- FPS capture requires Windows ETW permissions; the program does not request elevation.
- The overlay may not appear over exclusive fullscreen games.
- GPU utilization is the busiest 3D engine; a multi-GPU system is not attributed to a specific adapter.
- Temperature monitoring is not included.

## Third-party components
Project source and license: https://github.com/smety-dev/PC-Monitor
PresentMon 2.3.1 is distributed separately in tools with upstream MIT notice.
Qt/PySide6/Shiboken are dynamically linked; their respective licenses apply, not the project MIT license.
See licenses/ and build-dependencies.txt for included notices and exact versions.
Corresponding upstream sources: https://download.qt.io/official_releases/qt/ and https://download.qt.io/official_releases/QtForPython/
Python source: https://www.python.org/downloads/source/
PyInstaller source: https://github.com/pyinstaller/pyinstaller
Users may replace compatible shared libraries and debug modifications to LGPL components as permitted by their licenses.
Review actual bundled components, notices and corresponding-source availability before public distribution.
