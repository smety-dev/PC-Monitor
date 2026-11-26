"""Qt process controller for the optional official PresentMon console binary."""
import os
import time
import uuid
from PySide6.QtCore import QObject, QProcess, Signal
from frame_metrics import FrameStream
from gaming_benchmark import BenchmarkRecorder, MAX_ROWS
from diagnostics import LOG

from presentmon_bundle import bundled_exe, FROZEN
from presentmon_errors import capture_error


class Capture(QObject):
    changed = Signal(str)
    failed = Signal(str, str)
    benchmark_done = Signal(str, str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.errorOccurred.connect(self.error)
        self.process.finished.connect(self.finished)
        self.process.started.connect(lambda: self.changed.emit("Čekám na snímky vybraného procesu…"))
        self.benchmark = BenchmarkRecorder()
        self.stream = None
        self.pending = b""
        self.stderr = ""
        self.session = None
        self.exe = None
        self.stopping = False
        self.reported_failure = False

    def report_failure(self, message, details=""):
        if not self.reported_failure:
            self.reported_failure = True
            LOG.warning("PresentMon capture failed: %s", message)
            self.changed.emit("FPS měření selhalo.")
            self.failed.emit(message, details)

    @property
    def active(self):
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, pid):
        if self.active:
            return
        self.reported_failure = False
        if os.name != "nt":
            self.report_failure("PresentMon je dostupný pouze na Windows.")
            return
        exe = bundled_exe()
        if exe is None:
            self.report_failure("PresentMon chybí nebo není ověřen. Rozbal znovu celý balíček PC Monitor." if FROZEN else
                                "PresentMon není připraven. Spusť python presentmon_bundle.py.")
            return
        self.exe = str(exe.resolve())
        self.session = "PCMonitor-" + uuid.uuid4().hex
        self.stream = FrameStream(pid)
        self.pending = b""
        self.stderr = ""
        self.stopping = False
        self.changed.emit("Spouštím PresentMon…")
        self.process.start(self.exe, ["--process_id", str(pid), "--output_stdout",
            "--no_console_stats", "--v1_metrics", "--no_track_gpu", "--no_track_input",
            "--no_track_display", "--terminate_on_proc_exit", "--session_name", self.session])

    def read(self):
        chunk = bytes(self.process.readAllStandardOutput())
        self.pending += chunk
        parts = self.pending.split(b"\n")
        self.pending = parts.pop()
        if len(self.pending) > 65536:
            self.pending = b""
        if self.stream:
            received = time.monotonic()
            for part in parts:
                accepted = self.stream.feed(part.decode("utf-8", errors="replace"), received)
                if accepted and self.benchmark.active:
                    try:
                        self.benchmark.add(*self.stream.last_frame, received)
                        if self.benchmark.count >= MAX_ROWS:
                            self.stop_benchmark("Dosažen limit snímků.")
                    except (OSError, ValueError) as exc:
                        self.stop_benchmark("Chyba zápisu benchmarku.", exc)

    def start_benchmark(self, path, duration):
        if not self.active:
            raise RuntimeError("Nejprve spusť FPS měření na stránce Gaming.")
        self.benchmark.start(path, duration)

    def tick_benchmark(self):
        if not self.benchmark.active:
            return
        if not self.active:
            self.stop_benchmark("FPS měření skončilo.")
        elif self.benchmark.elapsed >= self.benchmark.duration:
            self.stop_benchmark("Časový limit dokončen.")
        else:
            try:
                self.benchmark.flush()
            except (OSError, ValueError) as exc:
                self.stop_benchmark("Chyba zápisu benchmarku.", exc)

    def stop_benchmark(self, reason="Benchmark zastaven.", error=None):
        if not self.benchmark.active:
            return
        path, count = self.benchmark.path, self.benchmark.count
        try:
            self.benchmark.stop()
        except (OSError, ValueError) as exc:
            error = exc
        if error is not None:
            LOG.warning("Benchmark write failed: %s", type(error).__name__)
            reason = "Chyba zápisu benchmarku. Soubor může být neúplný."
        self.benchmark_done.emit(path, reason, count)

    def read_error(self):
        self.stderr = (self.stderr + bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))[-2000:]

    def error(self, error):
        if not self.stopping and error == QProcess.ProcessError.FailedToStart:
            self.report_failure("PresentMon se nepodařilo spustit.", self.process.errorString())

    def finished(self, code, status):
        self.read()
        self.read_error()
        self.stop_benchmark("FPS měření skončilo; benchmark může být kratší.")
        self.stream = None
        if not self.stopping and not self.reported_failure:
            if code == 0 and status == QProcess.ExitStatus.NormalExit:
                self.changed.emit(capture_error(code, self.stderr))
            else:
                message = capture_error(code, self.stderr) if code != 0 else "PresentMon neočekávaně skončil."
                if message.startswith("PresentMon skončil"):
                    message = f"PresentMon neočekávaně skončil (kód {code})."
                self.report_failure(message, f"Exit code: {code}\n{self.stderr.strip()}")

    def snapshot(self):
        return self.stream.snapshot(time.monotonic()) if self.active and self.stream else None

    def stop(self):
        self.stopping = True
        self.stop_benchmark("FPS měření zastaveno; benchmark může být kratší.")
        if self.active:
            # Stop only our uniquely named ETW session; never the default or another tool's capture.
            cleanup = QProcess()
            cleanup.start(self.exe, ["--session_name", self.session, "--terminate_existing_session", "--no_console_stats"])
            if not cleanup.waitForFinished(2000):
                cleanup.kill()
                cleanup.waitForFinished(500)
            if not self.process.waitForFinished(1000):
                self.process.kill()
                self.process.waitForFinished(500)
        self.stream = None
        self.changed.emit("Měření zastaveno.")
