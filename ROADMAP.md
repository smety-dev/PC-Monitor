# PC Monitor — Roadmap

This is a proposal, not a promise of dates or version numbers.

## Available in v0.9.5

- Portable Windows x64 build and automated startup smoke test
- CPU, RAM, GPU 3D, disk and network monitoring
- Process inspection, CSV recording and offline analysis
- Gaming overlay, PresentMon capture and frame benchmarks

## Released: v0.9.6 — International Update

- [x] English and Czech interface translations, including dialogs, charts and overlay
- [x] Language selection with system-language fallback and saved preference
- [x] Both languages passed the initial Windows regression tests and manual checks; CSV schemas retained
- [x] Organize application modules, tests and build tooling into packages
- [x] Update English website and README preview
- [x] Reorganized Windows package built and published; GPU sampling issue reported afterward

## In validation: v0.9.7 — GPU Compatibility Hotfix

- [x] PowerShell module path isolation and WMI fallback
- [x] Original fix reported working on AMD Radeon RX 6600 XT (PR #19)
- [x] Regression tests for GPU providers, missing samples and process environment
- [ ] Pass Windows CI for the hotfix candidate
- [ ] Verify source and portable EXE against Task Manager 3D load on real hardware
- [ ] Review bundled third-party licenses and publish the hotfix

## Reliability and feedback

- [ ] Complete third-party redistribution license review
- [ ] Validate real-game FPS capture on Windows with authorized ETW access
- [ ] Test AMD, NVIDIA and Intel GPU configurations where available
- [ ] Test on additional Windows 10/11 systems
- [ ] Improve documentation using real application screenshots
- [ ] Collect and prioritize reproducible user reports

## Later: proposed features

- [ ] CPU/GPU temperatures using a supported, permission-aware method
- [ ] GPU memory metrics where supported
- [ ] Hardware and frame data correlation for benchmarks
- [ ] Optional signed Windows distribution if feasible

Ideas are welcome through [GitHub Issues](https://github.com/smety-dev/PC-Monitor/issues/new/choose). No feature or release date is guaranteed.
