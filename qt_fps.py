"""FPS capture panel shared with the gaming workspace."""
from i18n import tr
import psutil
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qt_theme import card, label, button, BLUE, GREEN, ORANGE, SPACE
from qt_pages import Plot
from qt_dialogs import ErrorDialog
from process_picker import ProcessPicker
from presentmon_capture import Capture
from presentmon_bundle import bundled_exe, FROZEN


class FpsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.capture = Capture(self)
        self.path = bundled_exe()
        self.target = None
        self.error_dialog = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 * SPACE)
        panel, body = card()
        body.addWidget(label(tr("Měření snímků / PresentMon"), "section"))
        row = QHBoxLayout()
        self.binary = label(tr("PresentMon 2.3.1 • ověřený modul") if self.path else tr("PresentMon chybí nebo není ověřen"), "muted")
        self.binary.setWordWrap(True)
        row.addWidget(self.binary, 1)
        self.check = button(tr("Zkontrolovat modul"))
        self.check.clicked.connect(self.check_module)
        row.addWidget(self.check)
        body.addLayout(row)
        row = QHBoxLayout()
        self.target_label = label(tr("Herní proces nebyl vybrán"), "muted")
        self.target_label.setWordWrap(True)
        row.addWidget(self.target_label, 1)
        self.pick = button(tr("Vybrat hru / aplikaci"))
        self.pick.clicked.connect(self.pick_process)
        row.addWidget(self.pick)
        body.addLayout(row)
        row = QHBoxLayout()
        self.start_button = button(tr("Spustit FPS měření"), True)
        self.start_button.clicked.connect(self.start)
        row.addWidget(self.start_button)
        self.stop_button = button(tr("Zastavit měření"))
        self.stop_button.clicked.connect(self.capture.stop)
        row.addWidget(self.stop_button)
        row.addStretch()
        body.addLayout(row)
        self.missing_hint = (tr("Modul chybí nebo je poškozen. Rozbal znovu celý balíček PC Monitor.") if FROZEN else
                             tr("Spusť python presentmon_bundle.py v terminálu projektu."))
        self.status = label(tr("Vyber běžící hru.") if self.path else self.missing_hint, "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        self.capture.changed.connect(lambda message: self.status.setText(tr(message)))
        self.capture.failed.connect(self.show_capture_error)
        layout.addWidget(panel)
        row = QGridLayout()
        row.setSpacing(SPACE)
        self.values = []
        for i, (title, color) in enumerate((("FPS / 1 s", GREEN), (tr("Průměr / 10 s"), BLUE), ("1% Low / 10 s", ORANGE), ("Frametime / 1 s", BLUE))):
            panel, body = card()
            body.addWidget(label(title, "metric"))
            value = label("—", "value")
            value.setStyleSheet("color: " + color)
            body.addWidget(value)
            self.values.append(value)
            row.addWidget(panel, i // 2, i % 2)
        row.setColumnStretch(0, 1)
        row.setColumnStretch(1, 1)
        layout.addLayout(row)
        panel, body = card()
        body.addWidget(label(tr("Frametime • posledních 120 snímků"), "section"))
        self.plot = Plot()
        body.addWidget(self.plot)
        self.note = label(tr("Měříme intervaly Present(), ne počet fyzicky zobrazených snímků."), "muted")
        self.note.setWordWrap(True)
        body.addWidget(self.note)
        layout.addWidget(panel)
        self.had_graph = False
        self.update_controls()

    def show_capture_error(self, message, details=""):
        if self.error_dialog is not None:
            return
        parent = self.window()
        self.error_dialog = ErrorDialog(parent, tr("FPS měření nelze spustit nebo pokračovat"),
                                        message, details)
        self.error_dialog.finished.connect(self.clear_error_dialog)
        self.error_dialog.open()

    def clear_error_dialog(self, *_):
        self.error_dialog = None

    def check_module(self):
        self.path = bundled_exe()
        self.binary.setText(tr("PresentMon 2.3.1 • ověřený modul") if self.path else tr("PresentMon chybí nebo není ověřen"))
        self.status.setText(tr("Modul připraven. Vyber hru.") if self.path else self.missing_hint)
        self.update_controls()
        if self.path is None:
            self.show_capture_error(self.missing_hint)

    def pick_process(self):
        if self.capture.active:
            return
        dialog = ProcessPicker(self, self.target)
        if dialog.exec() and dialog.selected:
            selected = dialog.selected
            self.target = (selected.pid, selected.created)
            self.target_label.setText(f"{selected.name}  ·  PID {selected.pid}")
            self.target_label.setToolTip(selected.title)
            self.update_controls()

    def start(self):
        target = self.target
        if not target or not self.path:
            self.status.setText(tr("Nejdříve připrav modul a vyber herní proces."))
            self.show_capture_error(self.status.text())
            return
        pid, created = target
        try:
            if psutil.Process(pid).create_time() != created:
                raise ValueError(tr("Proces byl nahrazen."))
        except (psutil.Error, OSError, ValueError):
            self.status.setText(tr("Proces již neběží. Vyber jej znovu."))
            self.show_capture_error(self.status.text())
            return
        self.capture.start(pid)
        self.update_controls()

    def update_controls(self):
        active = self.capture.active
        self.start_button.setEnabled(not active and self.path is not None and self.target is not None)
        self.stop_button.setEnabled(active)
        for widget in (self.check, self.pick):
            widget.setEnabled(not active)

    def refresh(self, visible=True, need_stats=True):
        if visible:
            self.update_controls()
        stats = self.capture.snapshot() if need_stats else None
        if visible and self.isVisible():
            values = (stats.fps, stats.average_fps, stats.low, stats.frametime) if stats else (None,)*4
            for i, (widget, value) in enumerate(zip(self.values, values)):
                widget.setText("—" if value is None else f"{value:.1f}" + (" ms" if i == 3 else ""))
            if stats:
                self.status.setText(tr(f"Měřím • {stats.count} vzorků / max. 10 s • swap chain {stats.chain}"))
                self.plot.render(list(range(1-len(stats.graph), 1)),
                                 [("Frametime", BLUE, stats.graph)], xlabel=tr("Snímky"), unit="ms")
                self.had_graph = True
            elif self.had_graph:
                self.plot.render([], [])
                self.had_graph = False
                if self.capture.active:
                    self.status.setText(tr("Čekám na nové snímky…"))
        return stats

    def shutdown(self):
        if self.error_dialog is not None:
            self.error_dialog.reject()
        self.capture.stop()
