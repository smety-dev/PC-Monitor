"""Timed game benchmarks and offline A/B comparison."""
from i18n import tr, decimal
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Event

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, QHeaderView, QProgressBar
from PySide6.QtGui import QColor, QBrush
from diagnostics import LOG
from gaming_benchmark import DURATIONS, analyze_benchmark, relative_change
from qt_dialogs import ErrorDialog
from qt_pages import Plot, table, populate
from qt_theme import card, label, button, BLUE, GREEN, ORANGE, DANGER, TEXT, MUTED, SPACE, workspace_tabs, workspace_tab


def formatted(value, suffix="", digits=2):
    return "—" if value is None else decimal(f"{value:.{digits}f}") + suffix


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
        layout.setSpacing(0)
        self.tabs = workspace_tabs(layout)
        layout = workspace_tab(self.tabs, tr("Měření"))
        results_layout = workspace_tab(self.tabs, tr("Výsledky A/B"))
        charts_layout = workspace_tab(self.tabs, tr("Grafy"))
        panel, body = card()
        body.addWidget(label(tr("1 · Připrav měření FPS"), "section"))
        hint = label(tr("Nejprve vyber hru a spusť FPS měření v Gaming. Potom zaznamenej stejnou herní scénu před a po změně nastavení."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        row = QHBoxLayout()
        self.capture_status = label(tr("FPS měření není spuštěno"), "muted")
        row.addWidget(self.capture_status, 1)
        go = button(tr("Otevřít měření FPS"))
        go.clicked.connect(open_gaming)
        row.addWidget(go)
        body.addLayout(row)
        layout.addWidget(panel)
        panel, body = card()
        body.addWidget(label(tr("2 · Zaznamenej herní scénu"), "section"))
        row = QHBoxLayout()
        row.addWidget(label(tr("Délka měření")))
        self.duration = QComboBox()
        for seconds in DURATIONS:
            self.duration.addItem(f"{seconds} s", seconds)
        self.duration.setCurrentIndex(1)
        row.addWidget(self.duration)
        self.start_button = button(tr("Spustit benchmark"), True)
        self.start_button.clicked.connect(self.start)
        self.stop_button = button(tr("Ukončit"))
        self.stop_button.clicked.connect(lambda: self.capture.stop_benchmark())
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        row.addStretch()
        body.addLayout(row)
        self.status = label(tr("Připraveno"), "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        body.addWidget(self.progress)
        self.last_file = label(tr("Žádný dokončený záznam"), "muted")
        self.last_file.setWordWrap(True)
        body.addWidget(self.last_file)
        layout.addWidget(panel)
        results = button(tr("Otevřít výsledky A/B"))
        results.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        body.addWidget(results)
        layout.addStretch()
        capture.benchmark_done.connect(self.finished)
        layout = results_layout

        panel, body = card()
        body.addWidget(label(tr("Porovnání měření A / B"), "section"))
        hint = label(tr("A je výchozí stav, B je nové měření. Načti benchmark CSV; běžné hardwarové CSV má jiný formát."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.file_labels = []
        self.load_buttons = []
        self.last_buttons = []
        self.summary_values = []
        summary = QHBoxLayout()
        summary.setSpacing(SPACE)
        for i, (title, color) in enumerate(((tr("A · VÝCHOZÍ"), BLUE), (tr("B · NOVÉ MĚŘENÍ"), GREEN))):
            tile, tile_body = card()
            tile_body.addWidget(label(title, "metric"))
            name = label(tr("Žádný soubor"), "muted")
            name.setWordWrap(True)
            tile_body.addWidget(name)
            self.file_labels.append(name)
            value = label("— FPS", "stat")
            value.setStyleSheet("color: " + color)
            tile_body.addWidget(value)
            detail = label("1% Low: —", "muted")
            tile_body.addWidget(detail)
            self.summary_values.append((value, detail))
            choose = button(tr("Načíst CSV"), True)
            choose.clicked.connect(lambda checked=False, slot=i: self.choose(slot))
            last = button(tr("Použít poslední záznam"))
            last.clicked.connect(lambda checked=False, slot=i: self.load(slot, self.last_path))
            tile_body.addWidget(choose)
            tile_body.addWidget(last)
            self.load_buttons.append(choose)
            self.last_buttons.append(last)
            summary.addWidget(tile, 1)
        body.addLayout(summary)
        self.analysis_status = label(tr("Načti výchozí měření A a potom nové měření B."), "muted")
        self.analysis_status.setWordWrap(True)
        body.addWidget(self.analysis_status)
        self.comparison_summary = label("", "section")
        self.comparison_summary.setWordWrap(True)
        body.addWidget(self.comparison_summary)
        graph_button = button(tr("Zobrazit grafy"))
        graph_button.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        body.addWidget(graph_button)
        layout.addWidget(panel)
        panel, body = card()
        body.addWidget(label(tr("Podrobné výsledky"), "section"))
        self.t = table([tr("Metrika"), "A", "B", tr("Změna B/A (%)")])
        self.t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.t.setMinimumHeight(480)
        body.addWidget(self.t)
        layout.addWidget(panel)
        layout.addStretch()
        layout = charts_layout
        panel, body = card()
        body.addWidget(label(tr("FPS v průběhu měření"), "section"))
        body.addWidget(label(tr("Průměrná snímková frekvence za každou sekundu."), "muted"))
        self.fps_plot = Plot()
        body.addWidget(self.fps_plot)
        layout.addWidget(panel)
        panel, body = card()
        body.addWidget(label(tr("Špičky frametime"), "section"))
        body.addWidget(label(tr("Nejdelší interval mezi snímky za každou sekundu (ms)."), "muted"))
        self.peak_plot = Plot()
        body.addWidget(self.peak_plot)
        note = label(tr("Stutter = frametime nejméně 33,333 ms a současně nejméně 2× medián daného měření. Špičky ≥ 50 ms jsou uvedeny zvlášť. Jde o orientační indikaci, nikoli důkaz konkrétní příčiny. Statistika používá pouze dominantní swap chain (nejvíce vzorků); porovnej také podíl snímků ≥ 50 ms, který má stejný práh v obou měřeních."), "muted")
        note.setWordWrap(True)
        body.addWidget(note)
        layout.addWidget(panel)
        layout.addStretch()
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
            self, tr("Uložit benchmark"), datetime.now().strftime("pc-monitor-benchmark-%Y%m%d-%H%M%S.csv"), "CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            self.capture.start_benchmark(path, self.duration.currentData())
        except (OSError, ValueError, RuntimeError) as exc:
            self.show_error(tr("Benchmark nelze spustit"), tr("Zkontroluj FPS měření, název souboru a oprávnění."), str(exc))
        else:
            self.progress.setValue(0)
            self.status.setText(tr("Benchmark běží. Vrať se do hry."))
        self.update_controls()

    def finished(self, path, reason, count):
        self.status.setText(tr(f"{reason} • {count:,} snímků").replace(",", " "))
        if reason.startswith("Časový limit"):
            self.progress.setValue(100)
        if count and not reason.startswith("Chyba"):
            self.last_path = path
            self.last_file.setText(tr("Poslední záznam: ") + Path(path).name)
        if reason.startswith("Chyba"):
            self.show_error(tr("Benchmark byl zastaven"), reason)
        self.update_controls()

    def update_controls(self):
        active = self.capture.benchmark.active
        self.capture_status.setText(tr("● FPS měření aktivní") if self.capture.active else tr("FPS měření není spuštěno"))
        tint = GREEN if self.capture.active else MUTED
        if self.capture_status.styleSheet() != "color: " + tint:
            self.capture_status.setStyleSheet("color: " + tint)
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
                self.status.setText(tr(f"● Probíhá měření · {recorder.elapsed:.0f} / {recorder.duration} s · {recorder.count} snímků"))
                self.progress.setValue(int(100 * recorder.elapsed / recorder.duration))
            self.update_controls()

    def choose(self, slot):
        path, _ = QFileDialog.getOpenFileName(self, tr("Načíst benchmark"), "", "CSV (*.csv)")
        if path:
            self.load(slot, path)

    def load(self, slot, path):
        if not path or self.future is not None or self.capture.benchmark.active or self.closing:
            return
        self.loading_slot = slot
        self.loading_name = Path(path).name
        self.cancel.clear()
        self.future = self.executor.submit(analyze_benchmark, path, self.cancel)
        self.analysis_status.setText(tr("Analyzuji benchmark…"))
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
            self.analysis_status.setText(tr("Načtení benchmarku selhalo."))
            self.show_error(tr("Neplatný benchmark"), tr("Soubor se nepodařilo analyzovat."), str(exc))
        else:
            i = self.loading_slot
            self.results[i] = result
            self.file_labels[i].setText(self.loading_name)
            self.file_labels[i].setToolTip(self.loading_name)
            self.analysis_status.setText(tr("Porovnávej stejnou scénu a podobnou délku měření. Změna je relativní vůči A; při nulovém A není definována."))
            self.render()
        finally:
            self.future = None
            self.update_controls()

    def render(self):
        a, b = self.results
        delta_fps = relative_change(a.fps, b.fps) if a and b else None
        delta_low = relative_change(a.low, b.low) if a and b else None
        summary = tr("Porovnání se zobrazí po načtení A i B.") if delta_fps is None else (
            tr(f"Průměr FPS: {delta_fps:+.1f} % · 1% Low: ") + ("—" if delta_low is None else f"{delta_low:+.1f} %"))
        self.comparison_summary.setText(decimal(tr(summary)) if delta_fps is not None else tr(summary))
        for result, (value, detail) in zip(self.results, self.summary_values):
            value.setText(formatted(result.fps if result else None, digits=1) + " FPS")
            detail.setText("1% Low: " + formatted(result.low if result else None, digits=1) + " FPS")
        rows = []
        change_colors = []
        for title, attr, unit, digits, compare in (
            (tr("Průměr FPS"), "fps", "", 1, "relative"),
            ("1% Low FPS", "low", "", 1, "relative"),
            (tr("Průměr frametime"), "average_ms", " ms", 2, "relative"),
            (tr("Medián frametime"), "median_ms", " ms", 2, "relative"),
            ("Max. frametime", "peak_ms", " ms", 2, "relative"),
            (tr("Stutter snímky"), "stutters", "", 0, None),
            (tr("Podíl stutterů"), "stutter_percent", " %", 2, "relative"),
            (tr("Práh stutteru"), "threshold_ms", " ms", 2, None),
            (tr("Snímky ≥ 50 ms"), "severe", "", 0, None),
            (tr("Podíl snímků ≥ 50 ms"), "severe_percent", " %", 2, "relative"),
            (tr("Snímky (dominantní / celkem)"), "count", "", 0, None),
            (tr("Časový rozsah"), "span", " s", 1, None),
        ):
            av = getattr(a, attr) if a else None
            bv = getattr(b, attr) if b else None
            change = relative_change(av, bv) if compare == "relative" else None
            delta = "—" if change is None else f"{change:+.1f} %"
            left, right = formatted(av, unit, digits), formatted(bv, unit, digits)
            if attr == "count":
                left = f"{a.count} / {a.total_count}" if a else "—"
                right = f"{b.count} / {b.total_count}" if b else "—"
            rows.append((title, left, right, decimal(delta)))
            color = TEXT
            if change is not None and change != 0:
                better = change > 0 if attr in ("fps", "low") else change < 0
                color = GREEN if better else DANGER
            change_colors.append(color)
        populate(self.t, rows)
        for i, color in enumerate(change_colors):
            self.t.item(i, 3).setForeground(QBrush(QColor(color)))
        present = [(name, color, result) for name, color, result in
                   (("A", BLUE, a), ("B", GREEN, b)) if result]
        length = max((len(result.fps_series) for _, _, result in present), default=0)
        x = list(range(length))
        for plot, attr in ((self.fps_plot, "fps_series"), (self.peak_plot, "peak_series")):
            lines = []
            for name, color, result in present:
                series = getattr(result, attr)
                lines.append((name, color, series + (None,) * (length - len(series))))
            plot.render(x, lines, xlabel=tr("Uplynulý čas (s)"), unit="FPS" if attr == "fps_series" else "ms")

    def shutdown(self):
        self.closing = True
        self.timer.stop()
        self.cancel.set()
        self.executor.shutdown(wait=False, cancel_futures=True)
        if self.error_dialog is not None:
            self.error_dialog.reject()
        self.capture.stop_benchmark("Aplikace ukončena.")
