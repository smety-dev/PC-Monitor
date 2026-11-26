"""Qt process controller for the optional official PresentMon console binary."""
import os
import time
import uuid
from PySide6.QtCore import QObject, QProcess, Signal
from frame_metrics import FrameStream

from presentmon_bundle import bundled_exe
from presentmon_errors import capture_error


class Capture(QObject):
    changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.errorOccurred.connect(self.error)
        self.process.finished.connect(self.finished)
        self.process.started.connect(lambda: self.changed.emit("Čekám na snímky vybraného procesu…"))
        self.stream = None
        self.pending = b""
        self.stderr = ""
        self.session = None
        self.exe = None
        self.stopping = False

    @property
    def active(self):
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, pid):
        if self.active:
            return
        if os.name != "nt":
            self.changed.emit("PresentMon je dostupný pouze na Windows.")
            return
        exe = bundled_exe()
        if exe is None:
            self.changed.emit("PresentMon není připraven. Spusť python presentmon_bundle.py.")
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
                self.stream.feed(part.decode("utf-8", errors="replace"), received)

    def read_error(self):
        self.stderr = (self.stderr + bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))[-2000:]

    def error(self, error):
        if not self.stopping:
            self.changed.emit("PresentMon: " + self.process.errorString())

    def finished(self, code, status):
        self.read_error()
        if not self.stopping:
            self.changed.emit(capture_error(code, self.stderr))
        self.stream = None

    def snapshot(self):
        return self.stream.snapshot(time.monotonic()) if self.active and self.stream else None

    def stop(self):
        self.stopping = True
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
