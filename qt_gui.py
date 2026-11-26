"""PC Monitor Qt desktop application."""
import sys
import time
from collections import deque
import psutil
from PySide6.QtCore import QTimer, QByteArray, Qt, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedWidget, QButtonGroup, QScrollArea, QProgressBar, QComboBox)
from qt_theme import BLUE, GREEN, ORANGE, MUTED, DANGER, SPACE, MetricCard, card, label, button, navigation_icon, configure_theme
from qt_monitor import Monitor
from diagnostics import configure_logging, LOG
from qt_gaming import GamingPage
from qt_benchmark import BenchmarkPage
from qt_settings import SettingsPage
from preferences import Preferences
from qt_pages import Processes, Recording, Analysis, Plot, fmt, configure_chart_fonts
from version import __version__


def page():
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(2 * SPACE)
    return widget, layout


def scroll(widget):
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(widget)
    return area


def rate(value):
    return "— MiB/s" if value is None else f"{value/1024**2:.2f}".replace(".", ",") + " MiB/s"


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"PC Monitor — {__version__}")
        self.resize(1250,820)
        self.setMinimumSize(900,650)
        self.prefs = Preferences()
        self.monitor = Monitor()
        self.history = deque(maxlen=61)
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0,0,0,0)
        shell.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 24, 16, 16)
        side.setSpacing(SPACE)
        side.addWidget(label("PC Monitor", "brand"))
        side.addWidget(label("PERFORMANCE STUDIO", "eyebrow"))
        side.addSpacing(SPACE)
        nav_content = QWidget()
        nav_content.setObjectName("navContent")
        nav = QVBoxLayout(nav_content)
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(4)
        self.nav_scroll = scroll(nav_content)
        self.nav_scroll.setObjectName("navScroll")
        self.nav_scroll.viewport().setObjectName("navViewport")
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side.addWidget(self.nav_scroll, 1)
        nav.addWidget(label("MONITORING", "eyebrow"))
        shell.addWidget(sidebar)
        main = QWidget()
        main.setObjectName("workspace")
        body = QVBoxLayout(main)
        body.setContentsMargins(24, 24, 24, 24)
        body.setSpacing(16)
        shell.addWidget(main,1)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(4)
        self.title = label("Přehled systému", "title")
        heading.addWidget(self.title)
        self.subtitle = label("", "subtitle")
        self.subtitle.setWordWrap(True)
        heading.addWidget(self.subtitle)
        header.addLayout(heading, 1)
        self.header_status = label("● Načítám", "status")
        header.addWidget(self.header_status, 0, Qt.AlignmentFlag.AlignTop)
        body.addLayout(header)
        self.stack = QStackedWidget()
        body.addWidget(self.stack,1)
        self.processes = Processes()
        self.recording = Recording()
        self.analysis = Analysis()
        self.gaming = GamingPage(self.monitor, self, self.prefs)
        self.benchmark = BenchmarkPage(self.gaming.fps.capture, self.open_fps)
        self.settings_page = SettingsPage(self.prefs, self.reset_preferences,
                                          self.open_overlay, lambda: self.navigate(5))
        self.recording.interval.setCurrentText(str(self.prefs.get("recording/interval")))
        self.recording.interval.currentTextChanged.connect(self.save_recording_interval)
        self.views = [
            ("Přehled","Přehled systému",scroll(self.overview()),"overview"),
            ("Procesor","Procesor",self.cpu_page(),"cpu"),
            ("Disky","Úložiště",self.disk_page(),"disks"),
            ("Síť","Síťový provoz",self.network_page(),"network"),
            ("Procesy","Správce procesů",self.processes,"processes"),
            ("Záznam","Záznam výkonu",scroll(self.recording),"recording"),
            ("Analýza","Analýza výkonu",scroll(self.analysis),"analysis"),
            ("Gaming","Herní režim",self.gaming,"gaming"),
            ("Benchmark","Herní benchmark",self.benchmark,"benchmark"),
            ("Nastavení","Nastavení aplikace",scroll(self.settings_page),"settings"),
        ]
        self.descriptions = (
            "Aktuální vytížení a provoz počítače na jednom místě.",
            "Frekvence a vytížení jednotlivých logických procesorů.",
            "Kapacita disků a rychlost čtení a zápisu.",
            "Aktuální příjem a odesílání dat.",
            "Najdi procesy, které nejvíce zatěžují počítač.",
            "Ulož průběh vytížení do souboru pro pozdější analýzu.",
            "Prozkoumej uložený záznam hardwarového výkonu.",
            "Měř FPS nebo zobraz výkon přímo při hraní.",
            "Změř a porovnej plynulost hry před a po změně nastavení.",
            "Přizpůsob chování aplikace svým potřebám.",
        )
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i,(name,title,widget,icon) in enumerate(self.views):
            if i == 5:
                nav.addSpacing(2 * SPACE)
                nav.addWidget(label("MĚŘENÍ", "eyebrow"))
            elif i == 7:
                nav.addSpacing(SPACE)
                nav.addWidget(label("HRANÍ", "eyebrow"))
            elif i == 9:
                nav.addSpacing(SPACE)
            self.stack.addWidget(widget)
            item = button(name)
            item.setObjectName("nav")
            item.setIcon(navigation_icon(icon))
            item.setIconSize(QSize(20, 20))
            item.setFixedHeight(40)
            item.setAccessibleName(name)
            item.setCheckable(True)
            self.group.addButton(item,i)
            item.clicked.connect(lambda checked=False,index=i:self.navigate(index))
            nav.addWidget(item)
        nav.addStretch()
        side.addSpacing(SPACE)
        side.addWidget(label("VERSION "+__version__, "eyebrow"))
        last = self.prefs.get("startup/last_page") if self.prefs.get("startup/remember_page") else "Přehled"
        index = next((i for i, view in enumerate(self.views) if view[0] == last), 0)
        self.navigate(index)
        self.restore_window_preferences()
        self.monitor.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def overview(self):
        widget, layout = page()
        row = QHBoxLayout()
        row.setSpacing(SPACE * 2)
        self.metrics = [MetricCard("Procesor", BLUE), MetricCard("Paměť RAM", ORANGE),
                        MetricCard("Grafika · 3D", GREEN)]
        for item in self.metrics:
            row.addWidget(item, 1)
        layout.addLayout(row)
        panel, body = card()
        heading = QHBoxLayout()
        heading.addWidget(label("Vytížení v čase", "section"))
        heading.addStretch()
        heading.addWidget(label("60 s", "eyebrow"))
        self.history_filter = QComboBox()
        self.history_filter.addItems(["Všechny metriky", "CPU", "RAM", "GPU"])
        self.history_filter.setAccessibleName("Zobrazené metriky grafu")
        self.history_filter.currentIndexChanged.connect(lambda *_: self.render_page())
        heading.addWidget(self.history_filter)
        body.addLayout(heading)
        self.plot = Plot()
        self.plot.setMinimumHeight(220)
        body.addWidget(self.plot, 1)
        layout.addWidget(panel, 1)
        row = QHBoxLayout()
        row.setSpacing(SPACE * 2)
        self.activity_values = []
        for title, captions, index in (
            ("Diskový provoz", ("Čtení", "Zápis"), 2),
            ("Síťový provoz", ("Příjem", "Odesílání"), 3),
        ):
            panel, body = card()
            header = QHBoxLayout()
            header.addWidget(label(title, "section"))
            header.addStretch()
            detail = button("Detail")
            detail.clicked.connect(lambda checked=False, target=index: self.navigate(target))
            header.addWidget(detail)
            body.addLayout(header)
            for caption in captions:
                line = QHBoxLayout()
                line.addWidget(label(caption, "muted"))
                line.addStretch()
                value = label("— MiB/s")
                line.addWidget(value)
                self.activity_values.append(value)
                body.addLayout(line)
            row.addWidget(panel, 1)
        layout.addLayout(row)
        panel, body = card()
        header = QHBoxLayout()
        header.addWidget(label("Informace o zařízení", "section"))
        header.addStretch()
        self.hardware = label("Detekuji hardware…", "muted")
        self.hardware.setWordWrap(True)
        body.addLayout(header)
        body.addWidget(self.hardware)
        layout.addWidget(panel)
        return widget

    def cpu_page(self):
        widget,layout = page()
        panel,body = card()
        body.addWidget(label("Frekvence procesoru","section"))
        self.freq = label("N/A","value")
        body.addWidget(self.freq)
        body.addWidget(label(f"{psutil.cpu_count(logical=False)} fyzických jader / {psutil.cpu_count()} vláken · frekvence hlášená OS","muted"))
        layout.addWidget(panel)
        panel,body = card()
        body.addWidget(label("Logické procesory","section"))
        self.core_grid = QGridLayout()
        self.core_grid.setSpacing(16)
        body.addLayout(self.core_grid)
        self.cores = []
        layout.addWidget(panel)
        layout.addStretch()
        return scroll(widget)

    def disk_page(self):
        widget,layout = page()
        panel,body = card()
        body.addWidget(label("Celkový diskový provoz","section"))
        self.disk_rate = [label("—", "value"), label("—", "value")]
        rates = QHBoxLayout()
        for title, value in zip(("Čtení", "Zápis"), self.disk_rate):
            column = QVBoxLayout()
            column.addWidget(label(title, "metric"))
            column.addWidget(value)
            rates.addLayout(column, 1)
        body.addLayout(rates)
        layout.addWidget(panel)
        self.drives = QVBoxLayout()
        layout.addLayout(self.drives)
        self.drive_widgets = {}
        layout.addStretch()
        return scroll(widget)

    def network_page(self):
        widget,layout = page()
        row = QHBoxLayout()
        self.net = []
        for name,color in (("PŘÍJEM",BLUE),("ODESÍLÁNÍ",GREEN)):
            panel,body = card()
            body.addWidget(label(name,"muted"))
            value = label("N/A","value")
            value.setStyleSheet("color: "+color)
            body.addWidget(value)
            self.net.append(value)
            row.addWidget(panel,1)
        layout.addLayout(row)
        layout.addStretch()
        return widget

    def save_recording_interval(self, value):
        self.prefs.set("recording/interval", value)
        self.prefs.sync()

    def restore_window_preferences(self):
        if self.prefs.get("startup/remember_geometry"):
            geometry = self.prefs.geometry()
            if isinstance(geometry, QByteArray) and self.restoreGeometry(geometry):
                return
        self.default_geometry()

    def default_geometry(self):
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.resize(1250, 820)
        screen = QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            self.resize(min(1250, area.width()), min(820, area.height()))
            self.move(area.center() - self.rect().center())

    def reset_preferences(self):
        if self.recording.recorder.active:
            return False
        self.prefs.reset()
        self.gaming.load_preferences()
        self.recording.interval.setCurrentText(str(self.prefs.get("recording/interval")))
        self.default_geometry()
        return True

    def open_fps(self):
        self.gaming.tabs.setCurrentIndex(0)
        self.navigate(7)

    def open_overlay(self):
        self.gaming.tabs.setCurrentIndex(1)
        self.navigate(7)

    def navigate(self,index):
        selected = self.group.button(index)
        selected.setChecked(True)
        self.nav_scroll.ensureWidgetVisible(selected, 0, 4)
        self.stack.setCurrentIndex(index)
        self.monitor.set_process_visible(index == 4 and not self.isMinimized())
        self.prefs.set("startup/last_page", self.views[index][0])
        self.prefs.sync()
        self.title.setText(self.views[index][1])
        self.subtitle.setText(self.descriptions[index])
        if hasattr(self,"timer"):
            self.render_page()

    def refresh(self):
        self.monitor.set_process_visible(self.stack.currentIndex() == 4 and not self.isMinimized())
        if self.hardware.text() != self.monitor.hardware:
            self.hardware.setText(self.monitor.hardware)
        basic = self.monitor.basic
        if basic is not None:
            cpu,ram = basic
            gpu = self.monitor.gpu
            self.recording.capture(cpu,ram,gpu,self.monitor.advanced)
            now = time.monotonic()
            self.history.append((now, cpu, ram.percent, gpu))
            while self.history and self.history[0][0] < now - 60:
                self.history.popleft()
        recording = self.recording.recorder.active
        self.benchmark.refresh(self.stack.currentIndex() == 8 and not self.isMinimized())
        benchmarking = self.gaming.fps.capture.benchmark.active
        self.gaming.refresh(basic, self.monitor.gpu, self.monitor.advanced, recording or benchmarking, not self.isMinimized())
        state = ("● Benchmark probíhá" if benchmarking else "● Záznam probíhá" if recording else
                 "● Herní režim" if self.gaming.enabled else "● Živé měření" if basic is not None else "● Načítám")
        if self.header_status.text() != state:
            self.header_status.setText(state)
        color = DANGER if recording or benchmarking else GREEN if basic is not None else MUTED
        style = "color: " + color
        if self.header_status.styleSheet() != style:
            self.header_status.setStyleSheet(style)
        if not self.isMinimized():
            self.render_page()

    def render_page(self):
        index = self.stack.currentIndex()
        basic = self.monitor.basic
        sample = self.monitor.advanced or {}
        if index == 0 and basic is not None:
            cpu,ram = basic
            self.metrics[0].set_value(cpu,f"{psutil.cpu_count(logical=False)} jader / {psutil.cpu_count()} vláken")
            self.metrics[1].set_value(ram.percent, f"{ram.available/1024**3:.1f} GiB volných z {ram.total/1024**3:.1f} GiB")
            gpu = self.monitor.gpu
            self.metrics[2].set_value(gpu, "Nejvytíženější 3D jednotka" if gpu is not None else "GPU data nedostupná")
            rates = (*(sample.get("disk_rates") or (None, None)), *(sample.get("net_rates") or (None, None)))
            for widget, value in zip(self.activity_values, rates):
                widget.setText(rate(value) if value is not None else "— MiB/s")
            selected = self.history_filter.currentIndex()
            if self.history:
                latest = self.history[-1][0]
                x = []
                samples = []
                for timestamp, *values in self.history:
                    elapsed = timestamp - latest
                    if x and elapsed - x[-1] > 3:
                        x.append((x[-1] + elapsed) / 2)
                        samples.append((None, None, None))
                    x.append(elapsed)
                    samples.append(values)
                lines = [(name, color, [row[j] for row in samples])
                         for j, (name, color) in enumerate((("CPU", BLUE), ("RAM", ORANGE), ("GPU", GREEN)))
                         if selected == 0 or selected == j + 1]
                self.plot.render(x, lines, True, "", rolling_seconds=60)
        elif index == 1:
            frequency = sample.get("frequency")
            self.freq.setText(fmt(frequency,0)+" MHz" if frequency is not None else "N/A")
            cores = sample.get("cores",[])
            if len(cores)!=len(self.cores):
                while self.core_grid.count():
                    item = self.core_grid.takeAt(0)
                    item.widget().deleteLater()
                self.cores.clear()
                for i in range(len(cores)):
                    container = QWidget()
                    line = QVBoxLayout(container)
                    line.setContentsMargins(0,0,0,0)
                    name = label(f"CPU {i:02d}","muted")
                    bar = QProgressBar()
                    bar.setTextVisible(False)
                    line.addWidget(name)
                    line.addWidget(bar)
                    self.core_grid.addWidget(container,i//3,i%3)
                    self.cores.append((name,bar))
            for i,(value,(name,bar)) in enumerate(zip(cores,self.cores)):
                name.setText(f"CPU {i:02d}   ·   {value:.1f}%")
                bar.setValue(int(value))
        elif index == 2:
            read,write = sample.get("disk_rates") or (None,None)
            for widget, value in zip(self.disk_rate, (read, write)):
                widget.setText(rate(value))
            drives = sample.get("drives",[])
            mounts = {d[0] for d in drives}
            for mount in list(self.drive_widgets):
                if mount not in mounts:
                    self.drive_widgets.pop(mount)[0].deleteLater()
            for mount,used,total,percent in drives:
                if mount not in self.drive_widgets:
                    panel,body = card()
                    body.addWidget(label("Disk "+mount,"section"))
                    val = label("","muted")
                    body.addWidget(val)
                    bar = QProgressBar()
                    bar.setTextVisible(False)
                    body.addWidget(bar)
                    self.drives.addWidget(panel)
                    self.drive_widgets[mount] = panel,val,bar
                _,val,bar = self.drive_widgets[mount]
                val.setText(f"{used/1024**3:.1f} / {total/1024**3:.1f} GiB · {percent:.1f}%")
                bar.setValue(int(percent))
        elif index == 3:
            for widget,value in zip(self.net,sample.get("net_rates") or (None,None)):
                widget.setText(rate(value))
        elif index == 4:
            if self.monitor.gaming.is_set():
                self.processes.refresh(None)
                self.processes.status.setText("Sběr procesů pozastaven (Gaming Mode)")
            else:
                self.processes.refresh(self.monitor.processes)

    def closeEvent(self,event):
        if self.prefs.get("startup/remember_geometry"):
            self.prefs.save_geometry(self.saveGeometry())
        else:
            self.prefs.remove_geometry()
        self.prefs.sync()
        self.timer.stop()
        self.benchmark.shutdown()
        self.gaming.shutdown()
        self.monitor.close()
        self.recording.finish()
        self.analysis.shutdown()
        LOG.info("PC Monitor closed")
        super().closeEvent(event)


def main():
    configure_logging()
    LOG.info("PC Monitor %s started", __version__)
    app = QApplication(sys.argv)
    family = configure_theme(app)
    configure_chart_fonts(family)
    window = Window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
