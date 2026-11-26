# PC Monitor

A lightweight Windows application for real-time hardware performance monitoring, built with Python.

**Current version: v0.7.0 — Early development**

## Features

- Real-time CPU and RAM utilization
- GPU 3D utilization (Windows performance counters, busiest detected 3D engine)
- Automatic CPU and GPU name detection in the GUI
- Live performance charts with up to 60 samples
- Available and total RAM
- Physical and logical CPU core detection
- Dark user interface with utilization and temperature tabs
- Optional CPU/GPU temperature readings, history and session peaks via LibreHardwareMonitor

## Requirements

- Windows 10 or 11 (compatibility across systems has not been fully tested)
- Python 3.14 (development version used), with Tkinter
- PowerShell and Windows GPU performance counters
- psutil and matplotlib

## Installation

```powershell
python -m pip install -r requirements.txt
python gui.py
```

The legacy terminal monitor is also available with `python main.py`. It does not include the GUI-only features.

## Temperature monitoring

Download [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) from its official releases, extract it and run it alongside PC Monitor. Some sensors require LibreHardwareMonitor to run as administrator; do not bypass system security policies. No extra Python package is required.

The temperature tab reads available CPU package/control (or core fallback) and GPU core/edge sensors through WMI. On multi-device systems it reports the hottest matching reading for each category, not individual devices. Missing sensors display as unavailable. Colors at 80 and 90 °C are generic visual indicators, not hardware-specific safety limits. History contains up to 60 GUI samples, repeating the latest background reading between polls. Peaks are reset on restart.

## Versioning

The application version is defined in [`version.py`](version.py) and shared by both entry points. When releasing an update, update that file, the current version in this README, and [`CHANGELOG.md`](CHANGELOG.md). README and changelog updates are manual.

## Planned features

- Gaming overlay
- Improved user interface
- Standalone executable

## About

My first Python project, created to learn programming and develop useful PC gaming tools.
