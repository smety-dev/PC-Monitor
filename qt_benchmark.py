"""Timed game benchmarks and offline A/B comparison."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Event

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog
from diagnostics import LOG
from gaming_benchmark import DURATIONS, analyze_benchmark, relative_change
from qt_dialogs import ErrorDialog
from qt_pages import Plot, table, populate
from qt_theme import card, label, button, BLUE, GREEN, ORANGE


def formatted(value, suffix="", digits=2):
    return "—" if value is None else f"{value:.{digits}f}".replace(".", ",") + suffix


class BenchmarkPage(QWidget):
    def __init__(self, capture, open_gaming):
        super().__init__()
        self.capture = capture
        self.last_path = None
        self.results = [None, None]
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.cancel = Event()
        self.future = None
        self.loading_slot = None
        self.closing = False
        self.error_dialog = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        panel, body = card()
        body.addWidget(label("Herní benchmark", "section"))
        hint = label("Nejprve vyber hru a spusť FPS měření v Gaming. Potom zaznamenej stejnou herní scénu před a po změně nastavení.", "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        row = QHBoxLayout()
        self.capture_status = label("FPS měření není spuštěno", "muted")
        row.addWidget(self.capture_status, 1)
        go = button("Přejít na Gaming")
        go.clicked.connect(open_gaming)
        row.addWidget(go)
        body.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(label("Délka"))
        self.duration = QComboBox()
        for seconds in DURATIONS:
            self.duration.addItem(f"{seconds} s", seconds)
        self.duration.setCurrentIndex(1)
        row.addWidget(self.duration)
        self.start_button = button("Spustit benchmark", True)
        self.start_button.clicked.connect(self.start)
        self.stop_button = button("Ukončit")
        self.stop_button.clicked.connect(lambda: self.capture.stop_benchmark())
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        row.addStretch()
        body.addLayout(row)
        self.status = label("Připraveno", "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        self.last_file = label("Žádný dokončený záznam", "muted")
        self.last_file.setWordWrap(True)
        body.addWidget(self.last_file)
        layout.addWidget(panel)
        capture.benchmark_done.connect(self.finished)

        panel, body = card()
        body.addWidget(label("Porovnání měření A / B", "section"))
        hint = label("A je výchozí stav, B je nové měření. Načti benchmark CSV; běžné hardwarové CSV má jiný formát.", "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.file_labels = []
        self.load_buttons = []
        self.last_buttons = []
        for i, title in enumerate(("A – základ", "B – porovnání")):
            row = QHBoxLayout()
            name = label(title, "muted")
            name.setWordWrap(True)
            row.addWidget(name, 1)
            self.file_labels.append(name)
            choose = button("Načíst CSV")
            choose.clicked.connect(lambda checked=False, slot=i: self.choose(slot))
            last = button("Poslední záznam")
            last.clicked.connect(lambda checked=False, slot=i: self.load(slot, self.last_path))
            row.addWidget(choose)
            row.addWidget(last)
            self.load_buttons.append(choose)
            self.last_buttons.append(last)
            body.addLayout(row)
        self.analysis_status = label("Načti jedno nebo dvě měření.", "muted")
        self.analysis_status.setWordWrap(True)
        body.addWidget(self.analysis_status)
        self.t = table(["Metrika", "A", "B", "Změna B/A (%)"])
        self.t.setMinimumHeight(465)
        body.addWidget(self.t)
        layout.addWidget(panel)
        panel, body = card()
        body.addWidget(label("FPS / průměr intervalů v jednotlivých sekundách", "section"))
        self.fps_plot = Plot()
        body.addWidget(self.fps_plot)
        body.addWidget(label("Frametime / maximum v každé sekundě (ms)", "section"))
        self.peak_plot = Plot()
        body.addWidget(self.peak_plot)
        note = label("Stutter = frametime nejméně 33,333 ms a současně nejméně 2× medián daného měření. Špičky ≥ 50 ms jsou uvedeny zvlášť. Jde o orientační indikaci, nikoli důkaz konkrétní příčiny. Statistika používá pouze dominantní swap chain (nejvíce vzorků); porovnej také podíl snímků ≥ 50 ms, který má stejný práh v obou měřeních.", "muted")
        note.setWordWrap(True)
        body.addWidget(note)
        layout.addWidget(panel)
        self.render()
        self.update_controls()

    def show_error(self, title, message, details=""):
        if self.closing or self.error_dialog is not None:
            return
        self.error_dialog = ErrorDialog(self.window(), title, message, details)
        self.error_dialog.finished.connect(self.clear_error)
        self.error_dialog.open()

    def clear_error(self, *_):
        self.error_dialog = None

    def start(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Uložit benchmark", datetime.now().strftime("pc-monitor-benchmark-%Y%m%d-%H%M%S.csv"), "CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            self.capture.start_benchmark(path, self.duration.currentData())
        except (OSError, ValueError, RuntimeError) as exc:
            self.show_error("Benchmark nelze spustit", "Zkontroluj FPS měření, název souboru a oprávnění.", str(exc))
        else:
            self.status.setText("Benchmark běží. Vrať se do hry.")
        self.update_controls()

    def finished(self, path, reason, count):
        self.status.setText(f"{reason} • {count:,} snímků".replace(",", " "))
        if count and not reason.startswith("Chyba"):
            self.last_path = path
            self.last_file.setText("Poslední záznam: " + Path(path).name)
        if reason.startswith("Chyba"):
            self.show_error("Benchmark byl zastaven", reason)
        self.update_controls()

    def update_controls(self):
        active = self.capture.benchmark.active
        self.capture_status.setText("● FPS měření aktivní" if self.capture.active else "FPS měření není spuštěno")
        self.start_button.setEnabled(self.capture.active and not active and self.future is None and not self.closing)
        self.stop_button.setEnabled(active)
        self.duration.setEnabled(not active)
        for button_ in self.load_buttons:
            button_.setEnabled(self.future is None and not active and not self.closing)
        for button_ in self.last_buttons:
            button_.setEnabled(bool(self.last_path) and self.future is None and not active and not self.closing)

    def refresh(self, visible=True):
        self.capture.tick_benchmark()
        if visible:
            recorder = self.capture.benchmark
            if recorder.active:
                self.status.setText(f"● BENCHMARK   {recorder.elapsed:.0f} / {recorder.duration} s   ·   {recorder.count} snímků")
            self.update_controls()

    def choose(self, slot):
        path, _ = QFileDialog.getOpenFileName(self, "Načíst benchmark", "", "CSV (*.csv)")
        if path:
            self.load(slot, path)

    def load(self, slot, path):
        if not path or self.future is not None or self.capture.benchmark.active or self.closing:
            return
        self.loading_slot = slot
        self.loading_name = Path(path).name
        self.cancel.clear()
        self.future = self.executor.submit(analyze_benchmark, path, self.cancel)
        self.analysis_status.setText("Analyzuji benchmark…")
        self.update_controls()
        self.timer.start(100)

    def poll(self):
        if self.future is None or not self.future.done():
            return
        self.timer.stop()
        try:
            result = self.future.result()
        except Exception as exc:
            LOG.warning("Benchmark analysis failed: %s", type(exc).__name__)
            self.analysis_status.setText("Načtení benchmarku selhalo.")
            self.show_error("Neplatný benchmark", "Soubor se nepodařilo analyzovat.", str(exc))
        else:
            i = self.loading_slot
            self.results[i] = result
            self.file_labels[i].setText(f"{'AB'[i]}  •  {self.loading_name}")
            self.analysis_status.setText("Porovnávej stejnou scénu a podobnou délku měření. Změna je relativní vůči A; při nulovém A není definována.")
            self.render()
        finally:
            self.future = None
            self.update_controls()

    def render(self):
        a, b = self.results
        rows = []
        for title, attr, unit, digits, compare in (
            ("Průměr FPS", "fps", "", 1, "relative"),
            ("1% Low FPS", "low", "", 1, "relative"),
            ("Průměr frametime", "average_ms", " ms", 2, "relative"),
            ("Medián frametime", "median_ms", " ms", 2, "relative"),
            ("Max. frametime", "peak_ms", " ms", 2, "relative"),
            ("Stutter snímky", "stutters", "", 0, None),
            ("Podíl stutterů", "stutter_percent", " %", 2, "relative"),
            ("Práh stutteru", "threshold_ms", " ms", 2, None),
            ("Snímky ≥ 50 ms", "severe", "", 0, None),
            ("Podíl snímků ≥ 50 ms", "severe_percent", " %", 2, "relative"),
            ("Snímky (dominantní / celkem)", "count", "", 0, None),
            ("Časový rozsah", "span", " s", 1, None),
        ):
            av = getattr(a, attr) if a else None
            bv = getattr(b, attr) if b else None
            change = relative_change(av, bv) if compare == "relative" else None
            delta = "—" if change is None else f"{change:+.1f} %"
            left, right = formatted(av, unit, digits), formatted(bv, unit, digits)
            if attr == "count":
                left = f"{a.count} / {a.total_count}" if a else "—"
                right = f"{b.count} / {b.total_count}" if b else "—"
            rows.append((title, left, right, delta.replace(".", ",")))
        populate(self.t, rows)
        present = [(name, color, result) for name, color, result in
                   (("A", BLUE, a), ("B", GREEN, b)) if result]
        length = max((len(result.fps_series) for _, _, result in present), default=0)
        x = list(range(length))
        for plot, attr in ((self.fps_plot, "fps_series"), (self.peak_plot, "peak_series")):
            lines = []
            for name, color, result in present:
                series = getattr(result, attr)
                lines.append((name, color, series + (None,) * (length - len(series))))
            plot.render(x, lines, xlabel="Uplynulý čas (s)")

    def shutdown(self):
        self.closing = True
        self.timer.stop()
        self.cancel.set()
        self.executor.shutdown(wait=False, cancel_futures=True)
        if self.error_dialog is not None:
            self.error_dialog.reject()
        self.capture.stop_benchmark("Aplikace ukončena.")
