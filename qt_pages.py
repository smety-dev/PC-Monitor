"""Qt workspaces for process monitoring, recording and analysis."""
from i18n import tr, decimal
from datetime import datetime
from bisect import bisect_left
import math
from threading import Event
from diagnostics import LOG
from qt_dialogs import ErrorDialog
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QWheelEvent, QCursor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog,
    QAbstractScrollArea, QApplication, QToolTip)
from matplotlib import rcParams, font_manager
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, FuncFormatter, FixedLocator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from qt_theme import card, label, button, PANEL, TEXT, MUTED, BLUE, GREEN, ORANGE, GRID, SPACE
from process_metrics import filter_sort
from performance_logger import PerformanceRecorder
from performance_analysis import read_recording, summarize, utilization_hints


def configure_chart_fonts(family):
    # Matplotlib resolves font files separately from Qt; use an installed family.
    available = {entry.name for entry in font_manager.fontManager.ttflist}
    candidates = (family, "Segoe UI", "Inter", "Noto Sans", "DejaVu Sans")
    rcParams["font.family"] = list(dict.fromkeys(name for name in candidates if name in available)) or ["DejaVu Sans"]
    rcParams["font.size"] = 10


def table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels([tr(header) for header in headers])
    t.verticalHeader().hide()
    t.verticalHeader().setDefaultSectionSize(36)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    t.setWordWrap(False)
    t.setTextElideMode(Qt.TextElideMode.ElideRight)
    return t


def populate(t, rows):
    t.setUpdatesEnabled(False)
    try:
        for j in range(1, t.columnCount()):
            header = t.horizontalHeaderItem(j)
            if header is not None:
                header.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        t.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = t.item(i, j)
                if item is None:
                    item = QTableWidgetItem()
                    t.setItem(i, j, item)
                if item.text() != str(value):
                    item.setText(str(value))
                    item.setToolTip(str(value))
                if j:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    finally:
        t.setUpdatesEnabled(True)


def fmt(value, decimals=1):
    return "—" if value is None else decimal(f"{value:.{decimals}f}")


class Plot(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(7, 3), facecolor=PANEL)
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=.085, right=.915, top=.82, bottom=.20)
        self.setMinimumHeight(235)
        self._layout_key = None
        self._data_key = None
        self._artists = []
        self._hover_data = ((), (), False, "", None)
        self._hover_text = None
        self.mpl_connect("motion_notify_event", self.hover)
        self.mpl_connect("figure_leave_event", self.hide_hover)
        self.render([], [], True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "ax"):
            return
        width, height = max(1, self.width()), max(1, self.height())
        # Fixed logical-pixel gutters remain symmetric at different window sizes.
        gutter = min(.20, 54 / width)
        self.figure.subplots_adjust(left=gutter, right=1-gutter,
                                    top=1-min(.25, 30/height),
                                    bottom=min(.30, 38/height))
        self.draw_idle()

    def hide_hover(self, *_):
        if self._hover_text is not None:
            QToolTip.hideText()
            self._hover_text = None

    def hover(self, event):
        x, lines, percentage, unit, rolling = self._hover_data
        if event.inaxes is not self.ax or event.xdata is None or not x:
            self.hide_hover()
            return
        i = bisect_left(x, event.xdata)
        if i >= len(x):
            i = len(x)-1
        elif i and abs(x[i-1]-event.xdata) <= abs(x[i]-event.xdata):
            i -= 1
        # In the rolling view, don't snap the empty area to a distant sample.
        if rolling and abs(x[i]-event.xdata) > 2:
            self.hide_hover()
            return
        suffix = "%" if percentage else unit
        heading = (tr("Nejnovější vzorek") if abs(x[i]) < .05 else tr(f"{abs(x[i]):.1f} s zpět")) if rolling else f"{x[i]:.2f}".rstrip("0").rstrip(".")
        texts = [decimal(tr(heading))]
        for name, _, values in lines:
            value = values[i]
            if value is not None and math.isfinite(value):
                texts.append(f"{name}: {fmt(value, 1)}" + (" " + suffix if suffix else ""))
            else:
                texts.append(f"{name}: —")
        tooltip = "\n".join(texts)
        if tooltip != self._hover_text or not QToolTip.isVisible():
            QToolTip.showText(QCursor.pos(), tooltip, self)
            self._hover_text = tooltip

    def wheelEvent(self, event):
        # Matplotlib normally consumes the wheel for graph interactions.
        # Our plots are read-only; pass the original scroll deltas to the page.
        parent = self.parentWidget()
        while parent is not None and not isinstance(parent, QAbstractScrollArea):
            parent = parent.parentWidget()
        if parent is None:
            event.ignore()
            return
        viewport = parent.viewport()
        forwarded = QWheelEvent(
            QPointF(viewport.mapFromGlobal(event.globalPosition().toPoint())),
            event.globalPosition(), event.pixelDelta(), event.angleDelta(),
            event.buttons(), event.modifiers(), event.phase(), event.inverted(),
            event.source(), event.pointingDevice())
        QApplication.sendEvent(viewport, forwarded)
        event.accept()

    def render(self, x, lines, percentage=False, xlabel="Uplynulý čas (s)",
               *, unit="", rolling_seconds=None):
        # Retain axes and line artists across ordinary updates.
        xlabel = tr(xlabel)
        x = tuple(x)
        lines = [(tr(name), color, tuple(values)) for name, color, values in lines]
        layout_key = (percentage, xlabel, unit, rolling_seconds, tuple((name, color) for name, color, _ in lines))
        data_key = (x, tuple(values for _, _, values in lines))
        if layout_key == self._layout_key and data_key == self._data_key:
            return
        self._hover_data = (x, lines, percentage, unit, rolling_seconds)
        a = self.ax
        if layout_key != self._layout_key:
            a.clear()
            a.set_facecolor(PANEL)
            a.tick_params(colors=MUTED, labelsize=10, length=0, pad=6)
            a.set_axisbelow(True)
            a.grid(axis="y", color=GRID, alpha=.8, linewidth=.8)
            a.xaxis.set_major_locator(MaxNLocator(nbins=5))
            a.yaxis.set_major_locator(MaxNLocator(nbins=4))
            a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: decimal(f"{v:g}") + ("%" if percentage else "")))
            a.xaxis.set_major_formatter(FuncFormatter(lambda v, _: decimal(f"{v:g}")))
            if percentage:
                a.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
            if rolling_seconds:
                a.xaxis.set_major_locator(FixedLocator([-rolling_seconds, -.75*rolling_seconds, -.5*rolling_seconds, -.25*rolling_seconds, 0]))
                a.xaxis.set_major_formatter(FuncFormatter(lambda v, _: tr("Teď") if abs(v) < .01 else f"−{abs(v):g} s"))
            for spine in a.spines.values():
                spine.set_visible(False)
            a.set_xlabel(xlabel, color=MUTED, fontsize=9, labelpad=6)
            self._artists = [a.plot([], [], color=color, label=name, linewidth=2.0, solid_capstyle="round", solid_joinstyle="round")[0]
                             for name, color, _ in lines]
            if lines:
                a.legend(frameon=False, labelcolor=TEXT, loc="lower center",
                         bbox_to_anchor=(.5, 1.01), ncol=min(3, len(lines)), borderaxespad=0, fontsize=9)
            else:
                a.set_xticks([])
                a.set_yticks([])
                a.set_xlabel("")
                a.text(.5, .5, tr("Zatím nejsou k dispozici žádná data"), transform=a.transAxes,
                       ha="center", va="center", color=MUTED, fontsize=12)
        for artist, (_, _, values) in zip(self._artists, lines):
            artist.set_data(x, [float("nan") if value is None else value for value in values])
            if rolling_seconds and values and values[-1] is not None and math.isfinite(values[-1]):
                artist.set_marker("o")
                artist.set_markersize(4)
                artist.set_markevery([len(x)-1])
            else:
                artist.set_marker("." if len(x) == 1 else "None")
                artist.set_markevery(None)
        if lines:
            a.set_autoscalex_on(True)
            a.set_autoscaley_on(not percentage)
            a.relim()
            a.autoscale_view()
            if rolling_seconds:
                a.set_xlim(-rolling_seconds, 0)
            elif x:
                first, last = min(x), max(x)
                padding = (last - first) * .02 if first != last else .5
                a.set_xlim(first - padding, last + padding)
            if percentage:
                a.set_ylim(0, 100)
            else:
                a.set_ylim(0, max(1e-9, a.get_ylim()[1]))
        self._layout_key, self._data_key = layout_key, data_key
        self.draw_idle()


class Processes(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 * SPACE)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("Hledat podle názvu nebo PID…"))
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.status = label(tr("Čekám na data"), "muted")
        layout.addWidget(self.status)
        self.t = table([tr("Proces"), "PID", "CPU (%)", "RAM (MiB)"])
        self.t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1,2,3):
            self.t.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeMode.Fixed)
            self.t.setColumnWidth(i,110)
        layout.addWidget(self.t)
        hint = label(tr("Kliknutím na hlavičku seřadíš procesy. CPU je podíl celkového výkonu; RAM je rezidentní paměť (RSS). — znamená nedostupná data."), "muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.rows = None
        self.key = "cpu"
        self.desc = True
        self.t.horizontalHeader().setSortIndicatorShown(True)
        self.t.horizontalHeader().setSortIndicator(2,Qt.SortOrder.DescendingOrder)
        self.t.horizontalHeader().sectionClicked.connect(self.sort)
        self.search.textChanged.connect(self.render)

    def sort(self, index):
        key = ("name","pid","cpu","rss")[index]
        self.desc = not self.desc if key == self.key else key in ("cpu","rss")
        self.key = key
        self.t.horizontalHeader().setSortIndicator(index,Qt.SortOrder.DescendingOrder if self.desc else Qt.SortOrder.AscendingOrder)
        self.render()

    def refresh(self, rows):
        if rows is not self.rows:
            self.rows = rows
            self.render()

    def render(self, *_):
        rows = filter_sort(self.rows or (), self.search.text(), self.key, self.desc)
        populate(self.t, [(r.name,r.pid,fmt(r.cpu),fmt(None if r.rss is None else r.rss/1024**2)) for r in rows])
        self.status.setText(tr("Čekám na data") if self.rows is None else tr(f"{len(rows)} / {len(self.rows)} procesů"))


class Recording(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = PerformanceRecorder()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 * SPACE)
        panel, body = card()
        layout.addWidget(panel)
        body.addWidget(label(tr("Záznam výkonu do CSV"), "section"))
        self.status = label(tr("Připraveno k záznamu"), "status")
        body.addWidget(self.status)
        hint = label(tr("Zvol interval, spusť měření a vyber, kam uložit soubor CSV."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.stats = label(tr("0 vzorků  ·  0 s"), "value")
        body.addWidget(self.stats)
        controls = QHBoxLayout()
        controls.addWidget(label("Interval"))
        self.interval = QComboBox()
        self.interval.addItems(["1","2","5","10"])
        controls.addWidget(self.interval)
        controls.addWidget(label(tr("sekund"), "muted"))
        controls.addStretch()
        self.start_button = button(tr("Spustit záznam"),True)
        self.stop_button = button(tr("Zastavit"))
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        body.addLayout(controls)
        self.path = label(tr("Soubor zatím nebyl vybrán"),"muted")
        self.path.setWordWrap(True)
        body.addWidget(self.path)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.finish)
        panel, body = card()
        body.addWidget(label(tr("Ukládané metriky"),"section"))
        body.addWidget(label(tr("CPU · RAM · GPU 3D · frekvence CPU · disky · síť")))
        msg = label(tr("Záznam pokračuje při přepínání stránek. Data zůstávají v místním CSV."),"muted")
        msg.setWordWrap(True)
        body.addWidget(msg)
        layout.addWidget(panel)
        layout.addStretch()
        self.controls()

    def controls(self):
        active = self.recorder.active
        self.start_button.setEnabled(not active)
        self.stop_button.setEnabled(active)
        self.interval.setEnabled(not active)
        self.stats.setText(tr(f"{self.recorder.count} vzorků  ·  {self.recorder.elapsed:.0f} s"))
        self.status.setStyleSheet("color: " + (GREEN if active else MUTED))

    def start(self):
        path,_ = QFileDialog.getSaveFileName(self,tr("Uložit záznam"),datetime.now().strftime("pc-monitor-%Y%m%d-%H%M%S.csv"),"CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            self.recorder.start(path,int(self.interval.currentText()))
        except (OSError,ValueError,RuntimeError) as exc:
            LOG.warning("CSV start failed: %s", type(exc).__name__)
            ErrorDialog(self.window(), tr("Záznam nelze spustit"), tr("Zkontroluj cílový soubor a oprávnění."), str(exc)).exec()
            return
        self.path.setText(path)
        self.status.setText(tr("● Probíhá záznam"))
        self.controls()

    def finish(self):
        try:
            self.recorder.stop()
            self.status.setText(tr("Záznam ukončen"))
        except OSError as exc:
            LOG.warning("CSV close failed: %s", type(exc).__name__)
            self.status.setText(tr("Chyba při ukončování záznamu: ") + str(exc))
        self.controls()

    def capture(self,cpu,ram,gpu,advanced):
        if self.recorder.active:
            try:
                self.recorder.record(cpu,ram.percent,ram.available,gpu,advanced)
                self.controls()
            except (OSError,ValueError) as exc:
                self.finish()
                LOG.warning("CSV write failed: %s", type(exc).__name__)
                self.status.setText(tr("Chyba zápisu: ")+str(exc))
                ErrorDialog(self.window(), tr("Záznam byl zastaven"), tr("Zápis do CSV selhal."), str(exc)).exec()


GROUPS = {
    "Vytížení (%)": (("cpu_percent","CPU",BLUE),("ram_percent","RAM",ORANGE),("gpu_3d_percent","GPU 3D",GREEN)),
    "Disky (MiB/s)": (("disk_read_mib_s","Čtení",BLUE),("disk_write_mib_s","Zápis",ORANGE)),
    "Síť (MiB/s)": (("net_receive_mib_s","Příjem",BLUE),("net_send_mib_s","Odesílání",GREEN)),
    "Frekvence (MHz)": (("cpu_frequency_mhz","CPU",BLUE),),
    "Dostupná RAM (MiB)": (("ram_available_mib","RAM",ORANGE),),
}


def analyze(path, cancel=None):
    rows,skipped = read_recording(path, cancel)
    stats = summarize(rows, cancel)
    return rows,skipped,stats,utilization_hints(rows,stats,cancel)


class Analysis(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 * SPACE)
        self.rows = []
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.cancel = Event()
        self.future = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        bar = QHBoxLayout()
        self.open_button = button(tr("Načíst CSV"),True)
        self.open_button.clicked.connect(self.open)
        bar.addWidget(self.open_button)
        bar.addStretch()
        self.group = QComboBox()
        for key in GROUPS:
            self.group.addItem(tr(key), key)
        self.group.currentIndexChanged.connect(self.draw)
        bar.addWidget(self.group)
        layout.addLayout(bar)
        self.info = label(tr("Začni výběrem uloženého hardwarového CSV ze sekce Záznam."), "muted")
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        kpis = QHBoxLayout()
        self.kpis = {}
        for key,title,color in (("cpu_percent",tr("Průměr CPU"),BLUE),("gpu_3d_percent",tr("Průměr GPU"),GREEN),("ram_percent",tr("Průměr RAM"),ORANGE)):
            panel,body = card()
            body.addWidget(label(title,"muted"))
            value = label("—","value")
            value.setStyleSheet("color: "+color)
            body.addWidget(value)
            self.kpis[key] = value
            kpis.addWidget(panel)
        layout.addLayout(kpis)
        panel,body = card()
        body.addWidget(label(tr("Průběh měření"),"section"))
        self.plot = Plot()
        body.addWidget(self.plot)
        layout.addWidget(panel,1)
        self.t = table([tr("Metrika"),"Minimum",tr("Průměr"),"Maximum",tr("Vzorky")])
        self.t.setMinimumHeight(330)
        layout.addWidget(self.t)
        self.hints = label("", "muted")
        self.hints.setWordWrap(True)
        layout.addWidget(self.hints)

    def open(self):
        path,_ = QFileDialog.getOpenFileName(self,tr("Načíst záznam"),"","CSV (*.csv)")
        if not path or self.future is not None:
            return
        self.filename = Path(path).name
        self.open_button.setEnabled(False)
        self.info.setText(tr("Načítám…"))
        self.cancel.clear()
        self.future = self.executor.submit(analyze,path,self.cancel)
        self.timer.start(100)

    def poll(self):
        if self.future is None or not self.future.done():
            return
        self.timer.stop()
        try:
            rows,skipped,stats,hints = self.future.result()
        except Exception as exc:
            self.info.setText(tr("Načtení selhalo"))
            LOG.warning("CSV analysis failed: %s", type(exc).__name__)
            ErrorDialog(self.window(), tr("Neplatný záznam"), tr("Soubor se nepodařilo analyzovat."), str(exc)).exec()
        else:
            self.rows = rows
            self.info.setText(tr(f"{self.filename}  ·  {len(rows)} vzorků  ·  {rows[-1]['elapsed_s']:.1f} s  ·  vynecháno {skipped}"))
            for key,value in self.kpis.items():
                value.setText(fmt(stats[key][1])+" %" if stats[key] else "N/A")
            values = []
            for group,metrics in GROUPS.items():
                for key,name,_ in metrics:
                    stat = stats[key]
                    values.append((tr(name)+" "+group[group.index("("):],*(tuple(fmt(v,2) for v in stat[:3])+(stat[3],) if stat else ("N/A","N/A","N/A",0))))
            populate(self.t,values)
            self.hints.setText("\n".join(tr(hint) for hint in hints))
            self.draw()
        finally:
            self.future = None
            self.open_button.setEnabled(True)

    def draw(self,*_):
        if not self.rows:
            return
        step = max(1,(len(self.rows)+9999)//10000)
        rows = self.rows[::step]
        if rows[-1] is not self.rows[-1]:
            rows.append(self.rows[-1])
        group = self.group.currentData()
        self.plot.render([r["elapsed_s"] for r in rows],
                         [(tr(name),color,[r[key] for r in rows]) for key,name,color in GROUPS[group]],
                         group=="Vytížení (%)")

    def shutdown(self):
        self.timer.stop()
        self.cancel.set()
        self.executor.shutdown(wait=False,cancel_futures=True)
