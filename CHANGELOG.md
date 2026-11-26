# Changelog

Notable changes to PC Monitor are documented here. Earlier development milestones are reconstructed from the known project history; this is not a list of published GitHub Releases.

## [0.9.6]

### International Update
- Czech and English UI, with system-language default (Czech for cs, English otherwise).
- Language selector in Settings; changes apply on next launch, without interrupting active recordings.
- Translated navigation, monitoring, charts, recording, analysis, gaming overlay settings, benchmark and application dialogs.
- Language-neutral persisted page and corner values; existing Czech hardware and benchmark CSV formats remain unchanged.
- Regression tests for language resolution, persistence and both UI languages. Native Windows dialogs and external diagnostic text can retain their original language.
- Updated project website, README and build documentation, including an English demo dashboard.
- Organized runtime modules in `pc_monitor/`, tests in `tests/` and build tools in `scripts/`; retained `python main.py` and test discovery.

## [0.9.5]

### Release preparation
- Portable Windows x64 candidate built with PyInstaller onedir, original product icon and executable version metadata.
- Verified PresentMon bundled alongside the executable, with recovery guidance for packaged users.
- Windows CI runs regression tests and a packaged startup smoke test before creating the ZIP and SHA-256 checksum.
- Third-party notices and build dependency manifest included for pre-release review. Actual Windows compatibility, ETW capture and publication remain pending.

### Changed
- Unified dark palette, installed modern font selection, chart typography and spacing tokens.
- One consistent navigation icon tint in all Qt modes and states; scrollable sidebar for smaller windows.
- Polished tables, buttons, dialogs, gaming overlay and FPS metric layout.
- Compact overview metric cards, explicit units, live disk and network throughput, device details and a single clear page status.
- Separate FPS/overlay tabs and benchmark recording/results/graphs tabs with progress feedback and A/B summaries.
- Five offscreen GUI smoke tests with synthetic data and isolated preferences.
- Fixed 60-second overview timeline, selectable metrics, localized axis labels and hover readouts; gaps in sampling remain visible.

### Notes
- No new dependencies or capture changes. Windows visual verification pending.

## [0.9.4]

### Added
- Gaming Performance Analyzer workspace with 30/60/120/300-second timed per-frame benchmark recording using the existing PresentMon capture.
- Separate buffered benchmark CSV; dominant swap-chain statistics, average FPS, 1% low, frametime and adaptive/fixed hitch metrics.
- Offline A/B comparison with relative percentage changes, FPS and peak-frametime charts, synthetic demo generator and ten regression tests.

### Fixed
- Consistent relative percentage changes, symmetric plot margins and centered legends.
- Mouse-wheel scrolling over read-only charts in scrollable pages.

### Changed
- Replaced Windows stock navigation icons with consistent original high-DPI outline icons in theme colors.

### Notes
- Hardware CSV schema, dependencies and MIT license unchanged. No additional capture session.
- Stutter classification is heuristic; no CPU/GPU bottleneck inference or displayed-FPS claim.
- Windows ETW capture and benchmark GUI validation pending.

## [0.9.3]

### Changed
- Continuous GPU counter stream, stale-value expiry and bounded retry delay.
- Process sampling only while its page is visible; ten-second disk capacity cache.
- Reuse chart artists, skip identical updates and hidden gaming previews.
- Cache frame statistics and use partial selection for rolling 1% low.
- Cooperative CSV analysis cancellation and managed PowerShell shutdown.
- Shared themed CSV error dialogs and bounded local diagnostic logging.

### Notes
- No new pip dependencies or changes to CSV format.
- Windows runtime tests and CPU/RAM performance comparison pending.

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
