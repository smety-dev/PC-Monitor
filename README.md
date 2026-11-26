# PC Monitor

A lightweight Windows application for real-time hardware performance monitoring, built with Python.

**Current version: v0.8.2 — Early development**

## Features

- Real-time CPU and RAM utilization
- GPU 3D utilization (Windows performance counters, busiest detected 3D engine)
- Automatic CPU and GPU name detection in the GUI
- Live performance charts with up to 60 samples
- Available and total RAM
- Physical and logical CPU core detection
- Modern dark dashboard with circular gauges and dedicated Overview, CPU, Disks and Network pages
- OS-reported CPU frequency and per-logical-processor utilization
- Local disk capacity and aggregate disk read/write throughput
- Aggregate network receive/send throughput
- Read-only process manager with CPU and RAM usage, PID search and sortable columns

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

## Dashboard

The sidebar switches between the overview, CPU, disks, network and process pages. Charts retain up to 60 GUI samples; GPU data is polled independently and may repeat between updates. Hardware detection runs in the background. The dashboard uses existing Tkinter and matplotlib dependencies, with no extra installation required.

## Advanced monitoring

The hardware pages use psutil without requesting administrator privileges or installing a driver. Some metrics may be unavailable depending on system permissions and hardware. CPU frequency on Windows is OS-reported and may not represent instantaneous per-core clock speed. Disk and network throughput are aggregate counter differences over elapsed monotonic time; the first sample or a counter reset displays unavailable. Temperature monitoring remains experimental in a separate branch.

## Process manager

Search by process name or PID and click column headings to sort. CPU is normalized to the total logical CPU capacity (0–100%); the first sample is unavailable until a second reading. RAM is the resident working set (RSS) in MiB, not private memory. Protected processes may have unavailable readings. Sampling runs in a background thread; no process termination, administrator elevation or additional dependency is requested.

## Versioning

The application version is defined in [`version.py`](version.py) and shared by both entry points. When releasing an update, update that file, the current version in this README, and [`CHANGELOG.md`](CHANGELOG.md). README and changelog updates are manual.

## Planned features

- CPU and GPU temperatures
- Gaming overlay
- Standalone executable

## About

My first Python project, created to learn programming and develop useful PC gaming tools.
