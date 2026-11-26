"""Qt workspaces for process monitoring, recording and analysis."""
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog, QMessageBox)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from qt_theme import card, label, button, PANEL, TEXT, MUTED, BLUE, GREEN, ORANGE, GRID
from process_metrics import filter_sort
from performance_logger import PerformanceRecorder
from performance_analysis import read_recording, summarize, utilization_hints


def table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().hide()
    t.verticalHeader().setDefaultSectionSize(34)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return t


def populate(t, rows):
    t.setUpdatesEnabled(False)
    try:
        t.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = t.item(i, j)
                if item is None:
                    item = QTableWidgetItem()
                    t.setItem(i, j, item)
                item.setText(str(value))
                if j:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    finally:
        t.setUpdatesEnabled(True)


def fmt(value, decimals=1):
    return "N/A" if value is None else f"{value:.{decimals}f}"


class Plot(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(7, 3), facecolor=PANEL)
        super().__init__(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=.10, right=.97, top=.90, bottom=.18)
        self.setMinimumHeight(235)
        self.render([], [], True)

    def render(self, x, lines, percentage=False, xlabel="Uplynulý čas (s)"):
        a = self.ax
        a.clear()
        a.set_facecolor(PANEL)
        a.tick_params(colors=MUTED, length=0, pad=6)
        a.grid(axis="y", color=GRID, alpha=.7)
        for spine in a.spines.values():
            spine.set_visible(False)
        a.set_xlabel(xlabel, color=MUTED)
        for name, color, values in lines:
            a.plot(x, [float("nan") if v is None else v for v in values],
                   color=color, label=name, linewidth=1.8, marker="." if len(x)==1 else None)
        if percentage:
            a.set_ylim(0, 100)
        else:
            a.set_ylim(bottom=0)
        if not lines:
            a.set_xticks([])
            a.set_yticks([])
            a.set_xlabel("")
            a.text(.5, .5, "Zatím nejsou k dispozici žádná data", transform=a.transAxes,
                   ha="center", va="center", color=MUTED, fontsize=12)
        if lines:
            a.legend(frameon=False, labelcolor=TEXT, loc="upper left", ncol=min(3,len(lines)))
        self.draw_idle()


class Processes(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Vyhledat proces nebo PID")
        layout.addWidget(self.search)
        self.status = label("Čekám na data", "muted")
        layout.addWidget(self.status)
        self.t = table(["Proces", "PID", "CPU (%)", "RAM (MiB)"])
        self.t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1,2,3):
            self.t.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeMode.Fixed)
            self.t.setColumnWidth(i,110)
        layout.addWidget(self.t)
        layout.addWidget(label("CPU = podíl celkové kapacity • RAM = RSS • N/A = nedostupné", "muted"))
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
        self.status.setText("Čekám na data" if self.rows is None else f"{len(rows)} / {len(self.rows)} procesů")


class Recording(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = PerformanceRecorder()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        panel, body = card()
        layout.addWidget(panel)
        body.addWidget(label("Záznam výkonu do CSV", "section"))
        self.status = label("Připraveno", "muted")
        body.addWidget(self.status)
        self.stats = label("0 vzorků  ·  0 s", "value")
        body.addWidget(self.stats)
        controls = QHBoxLayout()
        controls.addWidget(label("Interval"))
        self.interval = QComboBox()
        self.interval.addItems(["1","2","5","10"])
        controls.addWidget(self.interval)
        controls.addWidget(label("sekund", "muted"))
        controls.addStretch()
        self.start_button = button("Spustit záznam",True)
        self.stop_button = button("Zastavit")
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        body.addLayout(controls)
        self.path = label("Soubor zatím nebyl vybrán","muted")
        self.path.setWordWrap(True)
        body.addWidget(self.path)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.finish)
        panel, body = card()
        body.addWidget(label("Ukládané metriky","section"))
        body.addWidget(label("CPU · RAM · GPU 3D · frekvence CPU · disky · síť"))
        msg = label("Záznam pokračuje při přepínání stránek. Data zůstávají v místním CSV.","muted")
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
        self.stats.setText(f"{self.recorder.count} vzorků  ·  {self.recorder.elapsed:.0f} s")

    def start(self):
        path,_ = QFileDialog.getSaveFileName(self,"Uložit záznam",datetime.now().strftime("pc-monitor-%Y%m%d-%H%M%S.csv"),"CSV (*.csv)")
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            self.recorder.start(path,int(self.interval.currentText()))
        except (OSError,ValueError,RuntimeError) as exc:
            QMessageBox.warning(self,"Záznam nelze spustit",str(exc))
            return
        self.path.setText(path)
        self.status.setText("● Probíhá záznam")
        self.controls()

    def finish(self):
        try:
            self.recorder.stop()
            self.status.setText("Záznam ukončen")
        except OSError as exc:
            self.status.setText(str(exc))
        self.controls()

    def capture(self,cpu,ram,gpu,advanced):
        if self.recorder.active:
            try:
                self.recorder.record(cpu,ram.percent,ram.available,gpu,advanced)
                self.controls()
            except (OSError,ValueError) as exc:
                self.finish()
                self.status.setText("Chyba zápisu: "+str(exc))


GROUPS = {
    "Vytížení (%)": (("cpu_percent","CPU",BLUE),("ram_percent","RAM",ORANGE),("gpu_3d_percent","GPU 3D",GREEN)),
    "Disky (MiB/s)": (("disk_read_mib_s","Čtení",BLUE),("disk_write_mib_s","Zápis",ORANGE)),
    "Síť (MiB/s)": (("net_receive_mib_s","Příjem",BLUE),("net_send_mib_s","Odesílání",GREEN)),
    "Frekvence (MHz)": (("cpu_frequency_mhz","CPU",BLUE),),
    "Dostupná RAM (MiB)": (("ram_available_mib","RAM",ORANGE),),
}


def analyze(path):
    rows,skipped = read_recording(path)
    stats = summarize(rows)
    return rows,skipped,stats,utilization_hints(rows,stats)


class Analysis(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.rows = []
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        bar = QHBoxLayout()
        self.open_button = button("Načíst CSV",True)
        self.open_button.clicked.connect(self.open)
        bar.addWidget(self.open_button)
        bar.addStretch()
        self.group = QComboBox()
        self.group.addItems(list(GROUPS))
        self.group.currentTextChanged.connect(self.draw)
        bar.addWidget(self.group)
        layout.addLayout(bar)
        self.info = label("Vyber záznam PC Monitoru", "muted")
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        kpis = QHBoxLayout()
        self.kpis = {}
        for key,title,color in (("cpu_percent","Průměr CPU",BLUE),("gpu_3d_percent","Průměr GPU",GREEN),("ram_percent","Průměr RAM",ORANGE)):
            panel,body = card()
            body.addWidget(label(title,"muted"))
            value = label("—","value")
            value.setStyleSheet("color: "+color)
            body.addWidget(value)
            self.kpis[key] = value
            kpis.addWidget(panel)
        layout.addLayout(kpis)
        panel,body = card()
        body.addWidget(label("Průběh měření","section"))
        self.plot = Plot()
        body.addWidget(self.plot)
        layout.addWidget(panel,1)
        self.t = table(["Metrika","Minimum","Průměr","Maximum","Vzorky"])
        self.t.setMinimumHeight(210)
        layout.addWidget(self.t)
        self.hints = label("", "muted")
        self.hints.setWordWrap(True)
        layout.addWidget(self.hints)

    def open(self):
        path,_ = QFileDialog.getOpenFileName(self,"Načíst záznam","","CSV (*.csv)")
        if not path or self.future is not None:
            return
        self.filename = Path(path).name
        self.open_button.setEnabled(False)
        self.info.setText("Načítám…")
        self.future = self.executor.submit(analyze,path)
        self.timer.start(100)

    def poll(self):
        if self.future is None or not self.future.done():
            return
        self.timer.stop()
        try:
            rows,skipped,stats,hints = self.future.result()
        except Exception as exc:
            self.info.setText("Načtení selhalo")
            QMessageBox.warning(self,"Neplatný záznam",str(exc))
        else:
            self.rows = rows
            self.info.setText(f"{self.filename}  ·  {len(rows)} vzorků  ·  {rows[-1]['elapsed_s']:.1f} s  ·  vynecháno {skipped}")
            for key,value in self.kpis.items():
                value.setText(fmt(stats[key][1])+" %" if stats[key] else "N/A")
            values = []
            for group,metrics in GROUPS.items():
                for key,name,_ in metrics:
                    stat = stats[key]
                    values.append((name+" "+group[group.index("("):],*(tuple(fmt(v,2) for v in stat[:3])+(stat[3],) if stat else ("N/A","N/A","N/A",0))))
            populate(self.t,values)
            self.hints.setText("\n".join(hints))
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
        group = self.group.currentText()
        self.plot.render([r["elapsed_s"] for r in rows],
                         [(name,color,[r[key] for r in rows]) for key,name,color in GROUPS[group]],
                         group=="Vytížení (%)")

    def shutdown(self):
        self.timer.stop()
        self.executor.shutdown(wait=False,cancel_futures=True)
