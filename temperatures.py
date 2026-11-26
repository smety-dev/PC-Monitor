"""Optional LibreHardwareMonitor temperature provider for Windows."""
import json
import math
import subprocess

COMMAND = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-CimInstance -Namespace 'root\LibreHardwareMonitor' -ClassName Sensor -Filter "SensorType = 'Temperature'" -ErrorAction Stop |
    Select-Object Name, Identifier, Value |
    ConvertTo-Json -Compress
"""


def select_temperatures(rows):
    """Return the hottest preferred CPU package and GPU core readings."""
    cpu = []
    cpu_fallback = []
    gpu = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        identifier = str(row.get("Identifier", "")).lower()
        name = str(row.get("Name", "")).lower()
        try:
            value = float(row.get("Value"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value) or not -30 <= value <= 150:
            continue
        if identifier.startswith(("/amdcpu/", "/intelcpu/")):
            if any(term in name for term in ("package", "tctl", "tdie", "core (tctl")):
                cpu.append(value)
            elif "core" in name and "distance" not in name:
                cpu_fallback.append(value)
        elif identifier.startswith(("/amdgpu/", "/nvidiagpu/", "/intelgpu/")):
            if name in ("gpu core", "gpu temperature", "gpu edge"):
                gpu.append(value)
    return (
        max(cpu or cpu_fallback, default=None),
        max(gpu, default=None),
    )


def read_temperatures():
    """Return (CPU, GPU) in Celsius; missing readings are None."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", COMMAND],
            capture_output=True, encoding="utf-8", timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW, check=True,
        )
        rows = json.loads(result.stdout.strip() or "[]")
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            return None, None
        return select_temperatures(rows)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None, None
