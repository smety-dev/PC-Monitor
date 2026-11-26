# Changelog

Notable changes to PC Monitor are documented here. Earlier development milestones are reconstructed from the known project history; this is not a list of published GitHub Releases.

## [0.9.2]

### Added
- Themed Settings workspace with startup preferences and confirmed reset.
- Local per-user QSettings persistence for geometry, last page, overlay options, process sampling preference and CSV interval.
- Validation of saved values, fallback for disconnected overlay monitors and seven preference tests.

### Notes
- No new dependencies. Active recording and gaming sessions are not restored automatically.
- Windows settings and geometry validation pending.

## [0.9.1]

### Added
- Optional official PresentMon 2.3.1 console integration with selected process/PID and private ETW session.
- Live present-rate FPS, rolling average, 1% low, frametime chart and overlay metrics.
- Bounded per-swap-chain frame buffers, dominant-chain selection, stale-data handling and seven unit tests.

### Changed
- Searchable capture-target dialog with window-title filter, PID search and optional background processes.
- Automatic discovery and SHA-256 verification of the bundled PresentMon; removed the manual executable picker.
- Source distribution builder includes PresentMon and upstream licensing notices.
- Localized ETW permission errors and four additional unit tests.
- Themed Qt error dialog with expandable, copyable technical details; routine capture statuses remain inline.

### Notes
- PresentMon is acquired at build/setup time from the fixed official release and included in the source ZIP. No new pip dependencies. ETW access-denied was confirmed on a restricted Windows PC; successful capture still requires validation on an authorized PC.
- Hardware CSV format is unchanged; frame metrics are live only. Present rate is not displayed FPS.

## [0.9.0]

### Added
- Gaming Mode workspace with click-through desktop overlay, live preview, monitor and corner selection, adjustable background opacity and optional details.
- CPU, GPU 3D, RAM and active recording indicators using the existing monitoring service.
- Optional suspension of process sampling while gaming; hardware and CSV recording remain active.
- Six unit tests for overlay helpers.

### Notes
- No new runtime dependencies. Windowed/borderless games are the intended use; exclusive fullscreen and anti-cheat compatibility are not guaranteed.
- FPS, frametimes and temperatures were not measured in this release. Overlay operation confirmed by the project owner on Windows.

## [0.8.4]

### Added
- PySide6 desktop interface with rounded cards, custom gauges, native tables and seven monitoring workspaces.
- Offline CSV analyzer supporting Czech and original English recordings.
- Selectable charts, sample statistics and cautious high-utilization hints.
- Background CSV loading and invalid-value handling.

### Fixed
- Dark chart placeholder before a recording is loaded.

### Changed
- `main.py` now launches the Qt application; removed the old Tkinter UI and terminal monitor.
- Added PySide6 to runtime requirements; retained psutil and matplotlib for monitoring and charts.
- Added automated version consistency checks.

### Notes
- Qt interface and 21 unit tests confirmed by the project owner on Windows.

## [0.8.3]

### Fixed
- Export readable Czech column names and decimal commas to avoid Czech Excel interpreting decimal measurements as dates.

### Added
- Recording page with start/stop controls, file selection, duration and sample count.
- Local CSV export of system utilization, CPU frequency and aggregate disk/network rates.
- Selectable 1, 2, 5 or 10 second interval, exclusive file creation and flush after each row.
- Recording continues across pages and closes on application exit.

### Notes
- Windows runtime validation pending; no new dependencies.

## [0.8.2]

### Fixed
- Keep process table headings readable when hovered or pressed.
- Exclude the Windows System Idle Process (PID 0) from CPU consumers.

### Added
- Read-only process manager with live CPU usage, RAM working set and PID.
- Search by name or PID and sortable columns.
- Background process sampling with unavailable values and PID reuse handling.

### Notes
- Windows UI and eight unit tests confirmed by the project owner.

## [0.8.1]

### Fixed
- Corrected horizontal progressbar style inheritance that interrupted dashboard refresh when opening hardware pages.

### Changed
- Modern dark dashboard with sidebar navigation and circular utilization gauges.
- Dedicated CPU, disk and network pages with visual meters instead of a text dump.
- Responsive chart and scrollable hardware pages.
- Hardware name detection moved to a background thread.
- GPU polling pause increased to two seconds to reduce process overhead.

### Notes
- Existing monitoring backend retained; no additional dependencies or elevation requested.
- Windows UI and existing unit tests confirmed by the project owner.

## [0.8.0]

### Added
- CPU frequency and utilization per logical processor.
- Local disk capacity and aggregate disk read/write rates.
- Aggregate network receive/send rates.
- Hardware and network tab with background sampling.

### Notes
- Based on v0.6.2; v0.7.0 temperature work remains experimental in a separate branch and is not included.
- Windows runtime, throughput and unit tests were confirmed by the project owner.

## [0.6.2]

### Added
- Automatic CPU and GPU name detection using Windows CIM in the GUI.
- Shared project version in `version.py`.

### Changed
- Updated and formatted README and documented version maintenance.
- Both GUI and legacy CLI display the shared project version.

## [0.6.1]

### Fixed
- Removed duplicate GUI update scheduling to prevent accumulating callbacks and freezing.

## [0.6.0]

### Added
- Live CPU, RAM and GPU 3D history charts with up to 60 samples.

## [0.5.x]

### Added
- Tkinter graphical interface with utilization meters and memory and CPU core information.
- Background GPU measurement.

## [0.4]

### Added
- GPU 3D utilization in the terminal monitor.

## [0.3 and earlier]

### Added
- Initial terminal monitor with CPU and RAM usage and repeated live updates.
