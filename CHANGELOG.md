# Changelog

Notable changes to PC Monitor are documented here. Earlier development milestones are reconstructed from the known project history; this is not a list of published GitHub Releases.

## [0.8.4]

### Added
- Offline CSV analyzer supporting Czech and original English recordings.
- Selectable utilization, disk, network, frequency and available-memory charts.
- Sample statistics and cautious high-utilization hints.
- Background CSV loading and invalid-value handling.

### Notes
- Windows validation pending. No additional dependencies.

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
