# PC Monitor

A lightweight Windows application for real-time hardware performance monitoring, built with Python.

**Current version: v0.9.0 — Early development**

## Features

- New Qt desktop interface with custom antialiased gauges, rounded cards, dark navigation and native tables
- Real-time CPU and RAM utilization
- GPU 3D utilization (Windows performance counters, busiest detected 3D engine)
- Automatic CPU and GPU name detection in the GUI
- Live performance charts with up to 60 samples
- Available and total RAM
- Physical and logical CPU core detection
- OS-reported CPU frequency and per-logical-processor utilization
- Local disk capacity and aggregate disk read/write throughput
- Aggregate network receive/send throughput
- Read-only process manager with CPU and RAM usage, PID search and sortable columns
- Local performance CSV recording with selectable sampling interval
- Offline performance analysis with charts and sample statistics
- Configurable gaming overlay and optional process-sampling suspension

## Requirements

- Windows 10 or 11 (compatibility across systems has not been fully tested)
- Python 3.14 (development version used), with PySide6 (Qt)
- PowerShell and Windows GPU performance counters
- psutil, matplotlib and PySide6

## Installation

```powershell
python -m pip install -r requirements.txt
python main.py
```

`main.py` is the canonical entry point. It launches the Qt desktop application.

## Dashboard

The sidebar switches between the overview, CPU, disks, network, process, recording, analysis and gaming pages. Charts retain up to 60 GUI samples; GPU data is polled independently and may repeat between updates. Hardware detection runs in the background. The new desktop interface uses PySide6 and matplotlib. 

## Advanced monitoring

The hardware pages use psutil without requesting administrator privileges or installing a driver. Some metrics may be unavailable depending on system permissions and hardware. CPU frequency on Windows is OS-reported and may not represent instantaneous per-core clock speed. Disk and network throughput are aggregate counter differences over elapsed monotonic time; the first sample or a counter reset displays unavailable. Temperature monitoring remains experimental in a separate branch.

## Process manager

Search by process name or PID and click column headings to sort. CPU is normalized to the total logical CPU capacity (0–100%); the first sample is unavailable until a second reading. RAM is the resident working set (RSS) in MiB, not private memory. Protected processes may have unavailable readings. Sampling runs in a background thread; no process termination, administrator elevation or additional dependency is requested.

## Performance recording

Open Záznam (Recording), select 1, 2, 5 or 10 seconds and choose a new CSV file. Existing files are never overwritten. Recording continues while navigating other pages and stops on application exit. CSV uses UTF-8 with BOM, semicolon separators, Czech column names, decimal commas for Czech Excel, local date/time to seconds, elapsed seconds and explicit metric units. For other locales, import CSV with semicolon delimiter and Czech decimal settings. Missing values are blank; GPU and advanced readings are independently polled and may repeat. Actual sampling times depend on GUI scheduling. Data stays local; no upload or administrator elevation is requested. Choose a writable local directory (not a network drive). No per-process data or temperatures are recorded.

## Performance analyzer

Open Analýza and load an original PC Monitor CSV file (Czech or older English headers). The analyzer displays sample counts, last elapsed time, minimum, arithmetic mean and maximum for available values, plus selectable graphs. Invalid elapsed-time rows are skipped; invalid metric cells are unavailable. The graph subsamples very long recordings for responsiveness; statistics use all accepted rows. Files are limited to 500,000 data rows. Utilization hints are heuristic, not a bottleneck diagnosis: FPS, frame times and per-core history are not recorded. No data is uploaded.

## Gaming Mode & Overlay

Open Gaming and enable Gaming Mode. Choose a connected monitor, corner, background opacity and optional CPU frequency/available RAM details. The click-through, non-activating overlay is a separate always-on-top desktop window, with live CPU, GPU 3D, RAM and recording status. It does not inject into games or alter their files. Use windowed or borderless fullscreen mode; exclusive fullscreen and some game/compositor or anti-cheat configurations may hide or disallow desktop overlays. Disable Gaming Mode from the main window (Alt+Tab if necessary); closing the application closes the overlay. Optionally suspend process sampling during play; this resumes on exit from Gaming Mode. The usual hardware sampling and CSV recording continue. No FPS, frame times or temperatures are measured, and performance improvements are not guaranteed. No administrator rights or new runtime dependencies are required. Overlay settings are session-only.

## Testing

```powershell
python -m unittest discover -v
```

Run the application and exercise all eight pages after installing requirements. The automated tests cover monitoring, CSV logic, overlay helpers and version metadata consistency.

## Versioning

The application version is defined in [`version.py`](version.py) and displayed by the Qt application. When releasing an update, update that file, the current version in this README, and [`CHANGELOG.md`](CHANGELOG.md). README and changelog updates are manual.

## Planned features

- CPU and GPU temperatures
- Actual FPS and frametime measurement
- Standalone executable

## About

My first Python project, created to learn programming and develop useful PC gaming tools.
