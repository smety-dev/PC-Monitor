"""GPU hotfix regressions; synthetic PowerShell inputs never require a physical GPU."""
import os
import shutil
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pc_monitor.ui.qt_monitor import GPU_COMMAND, Monitor


class GpuHotfixTests(unittest.TestCase):
    def test_child_uses_own_powershell_module_path(self):
        monitor = Monitor()
        child = Mock()
        with patch.dict(os.environ, {"PSModulePath": "inherited", "PC_MONITOR_TEST": "kept"}):
            with patch("pc_monitor.ui.qt_monitor.subprocess.Popen", return_value=child) as popen:
                self.assertIs(monitor.launch("test"), child)
            self.assertEqual(os.environ["PSModulePath"], "inherited")
        env = popen.call_args.kwargs["env"]
        self.assertFalse(any(key.upper() == "PSMODULEPATH" for key in env))
        self.assertEqual(env["PC_MONITOR_TEST"], "kept")
        self.assertIn(child, monitor.children)

    def test_worker_logs_provider_error_and_accepts_zero(self):
        monitor = Monitor()

        def lines():
            yield "GPU_ERROR: Get-Counter: unavailable"
            yield "GPU_ERROR: Get-Counter: unavailable"
            yield "0"
            self.assertEqual(monitor.gpu, 0)
            yield "N/A"
            self.assertIsNone(monitor.gpu)
            yield "42.5"
            self.assertEqual(monitor.gpu, 42.5)
            monitor.stop_event.set()

        child = SimpleNamespace(stdout=lines())
        with patch.object(monitor, "launch", return_value=child), \
             patch.object(monitor, "release") as release, \
             patch("pc_monitor.ui.qt_monitor.LOG.warning") as warning:
            monitor.gpu_worker()
        warning.assert_called_once_with("GPU counter: %s", "Get-Counter: unavailable")
        release.assert_called_once_with(child)
        self.assertIsNone(monitor.gpu)


@unittest.skipUnless(sys.platform == "win32" and shutil.which("powershell"),
                     "Windows PowerShell required for script integration tests")
class PowerShellGpuTests(unittest.TestCase):
    def run_script(self, script):
        env = {key: value for key, value in os.environ.items()
               if key.upper() != "PSMODULEPATH"}
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            env=env, capture_output=True, text=True, errors="replace", timeout=30)
        return result.returncode, result.stdout.splitlines(), result.stderr

    def test_synthetic_aggregation(self):
        function = GPU_COMMAND.split("$script:missingSamples = 0", 1)[0]
        code, lines, error = self.run_script(function + r"""
$samples = @(
    [pscustomobject]@{Name='pid_1_luid_a_eng_0_engtype_3D'; Value=25},
    [pscustomobject]@{Name='pid_2_luid_a_eng_0_engtype_3D'; Value=30},
    [pscustomobject]@{Name='pid_3_luid_b_eng_0_engtype_3D'; Value=40},
    [pscustomobject]@{Name='pid_4_luid_a_eng_1_engtype_Copy'; Value=99},
    [pscustomobject]@{Name='pid_5_luid_a_eng_0_engtype_3D'; Value=-1}
)
[void](Write-GpuSample $samples Name Value)
[void](Write-GpuSample @() Name Value)
[void](Write-GpuSample @([pscustomobject]@{Name='pid_1_luid_a_eng_0_engtype_3D'; Value=0}) Name Value)
""")
        self.assertEqual(code, 0, error)
        self.assertEqual(lines, ["55", "N/A", "0"])

    def test_missing_counters_trigger_wmi(self):
        mocks = r"""
function Get-Counter {
    param($Path, $SampleInterval, [switch]$Continuous)
    for ($i=0; $i -lt 3; $i++) {
        [pscustomobject]@{CounterSamples=@()}
    }
}
function Get-CimInstance {
    param($ClassName)
    if ($script:wmiCalled) { throw 'synthetic end' }
    $script:wmiCalled = $true
    [pscustomobject]@{Name='pid_1_luid_a_eng_0_engtype_3D'; UtilizationPercentage=37}
}
function Start-Sleep { param($Seconds) }
"""
        code, lines, error = self.run_script(mocks + GPU_COMMAND)
        self.assertEqual(code, 1, error)
        self.assertEqual(lines[:3], ["N/A"] * 3)
        self.assertTrue(lines[3].startswith("GPU_ERROR: Get-Counter:"))
        self.assertEqual(lines[4], "37")
        self.assertTrue(lines[5].startswith("GPU_ERROR: WMI:"))
