"""FPS capture panel shared with the gaming workspace."""
from pathlib import Path
import psutil
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog
from qt_theme import card, label, button, BLUE, GREEN, ORANGE
from qt_pages import Plot
from presentmon_capture import Capture, DEFAULT_EXE


class FpsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.capture = Capture(self)
        self.path = DEFAULT_EXE if DEFAULT_EXE.is_file() else None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        panel, body = card()
        body.addWidget(label("Měření snímků / PresentMon", "section"))
        row = QHBoxLayout()
        self.binary = label(self.path.name if self.path else "PresentMon není nastaven", "muted")
        self.binary.setWordWrap(True)
        row.addWidget(self.binary, 1)
        self.choose = button("Vybrat EXE")
        self.choose.clicked.connect(self.choose_file)
        row.addWidget(self.choose)
        body.addLayout(row)
        row = QHBoxLayout()
        self.target = QComboBox()
        self.target.setMinimumWidth(180)
        self.target.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.target.setMinimumContentsLength(18)
        row.addWidget(self.target, 1)
        self.reload = button("Obnovit procesy")
        self.reload.clicked.connect(self.refresh_processes)
        row.addWidget(self.reload)
        body.addLayout(row)
        row = QHBoxLayout()
        self.start_button = button("Spustit FPS měření", True)
        self.start_button.clicked.connect(self.start)
        row.addWidget(self.start_button)
        self.stop_button = button("Zastavit měření")
        self.stop_button.clicked.connect(self.capture.stop)
        row.addWidget(self.stop_button)
        row.addStretch()
        body.addLayout(row)
        self.status = label("Vyber oficiální konzolový PresentMon 2.3.1 a běžící hru.", "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        self.capture.changed.connect(self.status.setText)
        layout.addWidget(panel)
        row = QHBoxLayout()
        self.values = []
        for title, color in (("FPS / 1 s", GREEN), ("Průměr / 10 s", BLUE), ("1% Low / 10 s", ORANGE), ("Frametime / 1 s", BLUE)):
            panel, body = card()
            body.addWidget(label(title, "muted"))
            value = label("—", "value")
            value.setStyleSheet("color: " + color)
            body.addWidget(value)
            self.values.append(value)
            row.addWidget(panel, 1)
        layout.addLayout(row)
        panel, body = card()
        body.addWidget(label("Frametime • posledních 120 snímků", "section"))
        self.plot = Plot()
        body.addWidget(self.plot)
        self.note = label("Měříme intervaly Present(), ne počet fyzicky zobrazených snímků.", "muted")
        self.note.setWordWrap(True)
        body.addWidget(self.note)
        layout.addWidget(panel)
        self.had_graph = False
        self.update_controls()

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Vyber oficiální PresentMon", "", "EXE (*.exe)")
        if path:
            self.path = Path(path)
            self.binary.setText(self.path.name)
            self.update_controls()

    def refresh_processes(self):
        if self.capture.active:
            return
        previous = self.target.currentData()
        rows = []
        for proc in psutil.process_iter(["pid", "name", "create_time"], ad_value=None):
            info = proc.info
            if info["pid"] and info["name"] and info["create_time"] is not None:
                rows.append((info["name"], info["pid"], info["create_time"]))
        self.target.clear()
        self.target.addItem("Vyber herní proces…", None)
        for name, pid, created in sorted(rows, key=lambda r: (r[0].casefold(), r[1])):
            self.target.addItem(f"{name}  (PID {pid})", (pid, created))
        index = self.target.findData(previous)
        self.target.setCurrentIndex(max(0, index))
        self.update_controls()

    def start(self):
        target = self.target.currentData()
        if not target or not self.path:
            self.status.setText("Nejdříve vyber PresentMon a herní proces.")
            return
        pid, created = target
        try:
            if psutil.Process(pid).create_time() != created:
                raise ValueError("Proces byl nahrazen.")
        except (psutil.Error, OSError, ValueError):
            self.status.setText("Proces již neběží. Obnov seznam a vyber jej znovu.")
            return
        self.capture.start(self.path, pid)
        self.update_controls()

    def update_controls(self):
        active = self.capture.active
        self.start_button.setEnabled(not active and self.path is not None)
        self.stop_button.setEnabled(active)
        for widget in (self.choose, self.reload, self.target):
            widget.setEnabled(not active)

    def refresh(self):
        self.update_controls()
        stats = self.capture.snapshot()
        if self.isVisible():
            values = (stats.fps, stats.average_fps, stats.low, stats.frametime) if stats else (None,)*4
            for i, (widget, value) in enumerate(zip(self.values, values)):
                widget.setText("—" if value is None else f"{value:.1f}" + (" ms" if i == 3 else ""))
            if stats:
                self.status.setText(f"Měřím • {stats.count} vzorků / max. 10 s • swap chain {stats.chain}")
                self.plot.render(list(range(1-len(stats.graph), 1)),
                                 [("Frametime (ms)", BLUE, stats.graph)], xlabel="Snímky")
                self.had_graph = True
            elif self.had_graph:
                self.plot.render([], [])
                self.had_graph = False
                if self.capture.active:
                    self.status.setText("Čekám na nové snímky…")
        return stats

    def shutdown(self):
        self.capture.stop()
