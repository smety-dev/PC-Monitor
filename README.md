# PC Monitor

A lightweight Windows application for real-time hardware performance monitoring, built with Python.

**Current version: v0.8.0 — Early development**

## Features

- Real-time CPU and RAM utilization
- GPU 3D utilization (Windows performance counters, busiest detected 3D engine)
- Automatic CPU and GPU name detection in the GUI
- Live performance charts with up to 60 samples
- Available and total RAM
- Physical and logical CPU core detection
- Dark user interface with utilization and hardware tabs
- OS-reported CPU frequency and per-logical-processor utilization
- Local disk capacity and aggregate disk read/write throughput
- Aggregate network receive/send throughput

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

## Advanced monitoring

The hardware tab uses psutil without requesting administrator privileges or installing a driver. Some metrics may be unavailable depending on system permissions and hardware. CPU frequency on Windows is OS-reported and may not represent instantaneous per-core clock speed. Disk and network throughput are aggregate counter differences over elapsed monotonic time; the first sample or a counter reset displays unavailable. Temperature monitoring remains experimental in a separate branch.

## Versioning

The application version is defined in [`version.py`](version.py) and shared by both entry points. When releasing an update, update that file, the current version in this README, and [`CHANGELOG.md`](CHANGELOG.md). README and changelog updates are manual.

## Planned features

- CPU and GPU temperatures
- Gaming overlay
- Improved user interface
- Standalone executable

## About

My first Python project, created to learn programming and develop useful PC gaming tools.
