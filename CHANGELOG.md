# Changelog

Notable changes to PC Monitor are documented here. Earlier development milestones are reconstructed from the known project history; this is not a list of published GitHub Releases.

## [0.8.0]

### Added
- CPU frequency and utilization per logical processor.
- Local disk capacity and aggregate disk read/write rates.
- Aggregate network receive/send rates.
- Hardware and network tab with background sampling.

### Notes
- Based on v0.6.2; v0.7.0 temperature work remains experimental in a separate branch and is not included.
- Windows runtime validation is pending.

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
