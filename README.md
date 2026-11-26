# PC Monitor

A lightweight Windows application for real-time hardware performance monitoring, built with Python.

**Current version: v0.9.5 — Early development**

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
- Optional PresentMon-based live FPS, frametimes and rolling 1% low
- Persistent local preferences and themed settings workspace
- Lower-overhead background sampling, reusable plot artists and bounded local diagnostics
- Timed per-frame gaming benchmark CSV recording, stutter analysis and A/B comparison

## Requirements

- Windows 10 or 11 (compatibility across systems has not been fully tested)
- Python 3.14 (development version used), with PySide6 (Qt)
- PowerShell and Windows GPU performance counters
- psutil, matplotlib and PySide6

## Installation

```powershell
python -m pip install -r requirements.txt
python presentmon_bundle.py
python main.py
```

`main.py` is the canonical entry point. It launches the Qt desktop application. The preparation command is needed only for a source checkout (once); it downloads the fixed official PresentMon binary and upstream notices, validates the published SHA-256 and stores the files locally. Hardware monitoring can still run without PresentMon. No downloads or elevation occur at app startup.

## Dashboard

The sidebar switches between the overview, CPU, disks, network, process, recording, analysis, gaming, benchmark and settings pages. Charts retain up to 60 GUI samples; GPU data is polled independently and may repeat between updates. Hardware detection runs in the background. The new desktop interface uses PySide6 and matplotlib. 

## Advanced monitoring

The hardware pages use psutil without requesting administrator privileges or installing a driver. Some metrics may be unavailable depending on system permissions and hardware. CPU frequency on Windows is OS-reported and may not represent instantaneous per-core clock speed. Disk and network throughput are aggregate counter differences over elapsed monotonic time; the first sample or a counter reset displays unavailable. Temperature monitoring remains experimental in a separate branch.

## Process manager

Search by process name or PID and click column headings to sort. CPU is normalized to the total logical CPU capacity (0–100%); the first sample is unavailable until a second reading. RAM is the resident working set (RSS) in MiB, not private memory. Protected processes may have unavailable readings. Sampling runs in a background thread only while the process page is selected and the main window is not minimized (unless explicitly suspended by Gaming Mode); no process termination, administrator elevation or additional dependency is requested.

## Performance recording

Open Záznam (Recording), select 1, 2, 5 or 10 seconds and choose a new CSV file. Existing files are never overwritten. Recording continues while navigating other pages and stops on application exit. CSV uses UTF-8 with BOM, semicolon separators, Czech column names, decimal commas for Czech Excel, local date/time to seconds, elapsed seconds and explicit metric units. For other locales, import CSV with semicolon delimiter and Czech decimal settings. Missing values are blank; GPU and advanced readings are independently polled and may repeat. Actual sampling times depend on GUI scheduling. Data stays local; no upload or administrator elevation is requested. Choose a writable local directory (not a network drive). No per-process data or temperatures are recorded.

## Performance analyzer

Open Analýza and load an original PC Monitor CSV file (Czech or older English headers). The analyzer displays sample counts, last elapsed time, minimum, arithmetic mean and maximum for available values, plus selectable graphs. Invalid elapsed-time rows are skipped; invalid metric cells are unavailable. The graph subsamples very long recordings for responsiveness; statistics use all accepted rows. Files are limited to 500,000 data rows. Utilization hints are heuristic, not a bottleneck diagnosis: FPS, frame times and per-core history are not recorded. No data is uploaded.

## Gaming Mode & Overlay

Open Gaming and enable Gaming Mode. Choose a connected monitor, corner, background opacity and optional CPU frequency/available RAM details. The click-through, non-activating overlay is a separate always-on-top desktop window, with live CPU, GPU 3D, RAM and recording status. It does not inject into games or alter their files. Use windowed or borderless fullscreen mode; exclusive fullscreen and some game/compositor or anti-cheat configurations may hide or disallow desktop overlays. Disable Gaming Mode from the main window (Alt+Tab if necessary); closing the application closes the overlay. Optionally suspend process sampling during play; this resumes on exit from Gaming Mode. The usual hardware sampling and CSV recording continue. Frame metrics are available through the optional PresentMon capture below; temperatures are not measured and performance improvements are not guaranteed. Gaming Mode itself does not require administrator rights. Overlay preferences are restored between launches; active Gaming Mode and capture sessions are not restored.

## FPS & frametime capture (optional)

1. PresentMon 2.3.1 is included in the prepared source distribution or installed into a development checkout using `python presentmon_bundle.py`. The Gaming page automatically locates and verifies the included executable; there is no manual EXE picker. If the module is missing, run preparation and click Zkontrolovat modul.
2. Start your game, click Vybrat hru / aplikaci and search for its actual process (not the launcher) by name, window title or PID. The default filter shows processes with visible titled windows; enable the checkbox to include background processes, and use Obnovit to refresh the list.
3. Click Spustit FPS měření. Enable Gaming Mode if you want the FPS metrics in the overlay. Stop capture with Zastavit měření or close PC Monitor.

The capture uses the official console application's CSV stdout stream with legacy metrics, a private ETW session, and a selected PID. [PresentMon documentation](https://github.com/GameTechDev/PresentMon/blob/v2.3.1/README-ConsoleApplication.md). No injection or changes to game files. ETW access can be restricted on some systems; use only with authorized permissions, and check the status message if capture fails. No automatic elevation is requested. Confirmed ETW access-denied errors are explained in a themed Qt dialog in Czech, with expandable/copyable diagnostic details; on a managed PC request access from IT, or use an authorized administrator account on a personal PC. Other monitoring functions remain available.

FPS is 1000 divided by mean MsBetweenPresents in the most recent one-second window; average FPS uses the recent ten-second window. The 1% low is 1000 divided by the mean interval of the slowest ceil(1% of N) frames in that ten-second window (at least 100 frames). The dominant swap chain by recent present count is selected instead of combining chains. These are present-rate metrics, not displayed FPS, input latency, or an explicit frame-generation measurement. A gap in received data of more than three seconds clears live values. The chart displays the most recent 120 frames; the rolling buffer is bounded to 12,000 frames per swap chain. Capture runs independently of Gaming Mode and the existing hardware CSV recorder; FPS/frametimes are recorded separately through the Benchmark workspace; the existing hardware CSV format is unchanged. No extra pip packages are required. Windows capture and game compatibility require practical validation.

## Build a distributable source ZIP

```powershell
python presentmon_bundle.py --package
```

The script creates `dist/PC-Monitor-v0.9.5-source-windows-x64.zip` with application source, runtime requirements, verified official PresentMon executable, original upstream README/license and third-party notices. Extract the entire ZIP before running. Recipients only install the Python dependencies and run `python main.py`; they do not need to download or select PresentMon. This is a Python source distribution, not a standalone EXE installer. The executable is excluded from Git; it is acquired from the pinned official release during preparation. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). PC Monitor's own MIT license is unchanged.

## Settings & preferences

Open Nastavení to choose whether to restore the last selected page and the main window geometry. Gaming overlay monitor, corner, opacity, hardware details, FPS visibility, process sampling preference and CSV recording interval are saved automatically as they change. Window geometry is saved on normal application exit. Qt restores saved geometry on available screens; unavailable overlay monitors fall back to the primary screen. The preferred monitor can be restored when it is connected again.

Preferences are stored locally per Windows user using Qt QSettings (native Windows registry under HKEY_CURRENT_USER\\Software\\smety-dev\\PC Monitor). No new dependencies, network sync or administrator permissions are required. Reset requires confirmation, restores default preferences and geometry, and is unavailable while recording hardware CSV. It does not delete CSV files, PresentMon files or other registry keys. Active Gaming Mode, game process IDs, frame capture and CSV recording sessions are never automatically started on launch.

## Performance & stability

GPU 3D utilization uses one continuous PowerShell counter stream at two-second intervals instead of launching PowerShell for every sample. Counter failures retry with bounded backoff; stale values expire after eight seconds. The process list is sampled only while its page is visible, and existing Gaming Mode suspension still applies. Disk capacity is refreshed every ten seconds; CPU/RAM and disk/network throughput retain their one-second sampling cadence. Live plots reuse line artists and skip identical updates; hidden gaming previews do not redraw. Frame statistics are cached until new data arrives and use a partial selection of the slowest intervals for 1% low. Offline analysis checks cancellation when the window closes. CSV and PresentMon errors use the shared themed error dialog where applicable.

Local diagnostic messages are written to `%LOCALAPPDATA%/PC Monitor/logs/diagnostics.log` (512 KiB per file, two rotated backups). No telemetry is uploaded; logs do not store raw CSV contents or process lists. If storage is unavailable, diagnostics are disabled without stopping monitoring. Windows GPU counter availability, shutdown behavior and actual performance gains require testing on a real system; no benchmark numbers are claimed.

## Gaming Performance Analyzer

1. Start the game, select its process in Gaming and start FPS measurement. PresentMon still requires authorized ETW access.
2. Open Benchmark, select 30, 60, 120 or 300 seconds, click Spustit benchmark, choose a new local CSV and return to the game. Use the same scene and comparable conditions for each run. The benchmark continues when the main window is minimized; it stops at the time limit, on manual stop, when FPS capture ends, on application exit or at the 500,000-row safety cap.
3. Load the finished benchmark into slot A. Repeat with different settings and load into B. Compare average present-rate FPS, 1% low (at least 100 frames), mean/median/maximum frametime, adaptive stutter share and fixed ≥ 50 ms hitch share. All displayed changes are relative percentages calculated against A, including stutter and hitch shares. A zero baseline or unavailable value is displayed as unavailable.

The separate benchmark CSV contains elapsed seconds, swap-chain identifier and individual present intervals in milliseconds (UTF-8 BOM, semicolon delimiter, decimal comma). FPS is calculated from intervals, not separately sampled. Recording uses the existing capture stream and writes buffered batches; the first event per chain is excluded because its interval may cross the start boundary. Files are created exclusively and never overwritten. The capture duration is based on receipt time; chart time is based on PresentMon timestamps relative to the first observed event. Startup switching/loading can affect results; a stopped or failed capture may be incomplete. The analyzer selects the chain with the most valid samples across the file rather than mixing chains, so verify comparable gameplay and chain behavior. Results are present-rate metrics, not displayed FPS or GPU/CPU bottleneck proof.

A stutter is an interval ≥ max(33.333 ms, 2 × the median interval of that run). This is a heuristic, and its threshold may differ across runs. Fixed ≥ 50 ms hitch share uses an identical threshold in both runs. Charts show per-second average present rate and per-second maximum frametime, preserving spikes rather than averaging them away; gaps remain missing. Raw files are bounded to 500,000 rows, 256 chains and 300 seconds. Offline analysis runs in a worker; no additional capture process or packages are required. Hardware utilization is not synchronized with these frame samples, so the analyzer does not infer a CPU/GPU bottleneck.

To test the analyzer without ETW access, create **synthetic** demonstration recordings:

```powershell
python gaming_benchmark.py --demo
```

Load `pc-monitor-benchmark-demo-A.csv` and `pc-monitor-benchmark-demo-B.csv` into the two slots. These are generated example data, not actual game measurements. Existing files are preserved.

## Visual design

The overview shows utilization, available memory, disk and network throughput, a rolling history and device details. FPS capture and overlay controls occupy separate tabs; Benchmark separates recording, comparison and graphs, with a progress bar and a concise A/B summary. Existing CSV formats, sampling and permission requirements remain unchanged.

The shared Qt theme defines color, typography and spacing tokens. Navigation icons use one monochrome tint in every state, with selection conveyed by the button background and text. The application prefers an installed Segoe UI Variable font and falls back to other installed sans-serif families; charts use the same family when available to Matplotlib. The sidebar scrolls on smaller windows. Benchmark cards summarize A/B FPS and 1% low, and comparison colors indicate the direction of improvement. No font files, dependencies or capture changes are introduced.

## Testing

The UI smoke tests use an offscreen Qt window and synthetic metrics with an isolated settings store. They exercise navigation, tab routing, metric rendering and benchmark comparison without starting hardware workers, PresentMon or changing real user preferences. They do not replace manual visual and ETW validation on Windows.

```powershell
python -m unittest discover -v
```

Run the application and exercise all ten pages after installing requirements. The automated tests cover monitoring, CSV logic, overlay helpers, frame metric calculations, PresentMon bundle verification and error handling, preferences, performance/stability helpers, benchmark recording and analysis, and version metadata consistency.

## Versioning

The application version is defined in [`version.py`](version.py) and displayed by the Qt application. When releasing an update, update that file, the current version in this README, and [`CHANGELOG.md`](CHANGELOG.md). README and changelog updates are manual.

## Planned features

- CPU and GPU temperatures
- Frame metrics in recording and offline analysis
- Standalone executable

## About

My first Python project, created to learn programming and develop useful PC gaming tools.
