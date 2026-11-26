# Contributing to PC Monitor

Bug reports, feature requests and small focused pull requests are welcome.

## Report a bug

Use the bug report template in [Issues](https://github.com/smety-dev/PC-Monitor/issues/new/choose). Include your PC Monitor version, Windows version, reproduction steps, and expected versus actual behavior. For GPU or FPS issues, include hardware and ETW permission context where relevant.

Logs are stored locally under `%LOCALAPPDATA%/PC Monitor/logs/`. Review and redact personal paths or identifiers before sharing any log, screenshot or CSV. Never post credentials or private data.

## Development

Use a separate branch and keep changes focused. See [GUIDE.md](GUIDE.md) for setup and build instructions.

```powershell
python -m pip install -r requirements.txt
python presentmon_bundle.py
python -m unittest discover -v
python main.py
```

PresentMon setup is optional for hardware-only use. Do not bypass administrator restrictions. Keep existing CSV formats and permission behavior compatible unless a change is explicitly documented. Test relevant UI pages manually where possible. Do not commit generated executables, personal recordings or logs.

Submit a pull request explaining the change, test results and known limitations. Security issues should follow [SECURITY.md](SECURITY.md).
