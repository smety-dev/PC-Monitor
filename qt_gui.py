"""PC Monitor Qt desktop application."""
import sys
from collections import deque
import psutil
from PySide6.QtCore import QTimer, QByteArray, Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedWidget, QButtonGroup, QScrollArea, QProgressBar)
from qt_theme import STYLE, BLUE, GREEN, ORANGE, MetricCard, card, label, button, navigation_icon
from qt_monitor import Monitor
from diagnostics import configure_logging, LOG
from qt_gaming import GamingPage
from qt_benchmark import BenchmarkPage
from qt_settings import SettingsPage
from preferences import Preferences
from qt_pages import Processes, Recording, Analysis, Plot, fmt
from version import __version__


def page():
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0,0,0,0)
    layout.setSpacing(14)
    return widget, layout


def scroll(widget):
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(widget)
    return area


def rate(value):
    return "N/A" if value is None else f"{value/1024**2:.2f} MiB/s"


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"PC Monitor — {__version__}")
        self.resize(1250,820)
        self.setMinimumSize(900,650)
        self.prefs = Preferences()
        self.monitor = Monitor()
        self.history = deque(maxlen=60)
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0,0,0,0)
        shell.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18,26,18,20)
        nav.setSpacing(5)
        nav.addWidget(label("PC Monitor","section"))
        nav.addWidget(label("PERFORMANCE STUDIO","muted"))
        nav.addSpacing(16)
        nav.addWidget(label("MONITORING","muted"))
        shell.addWidget(sidebar)
        main = QWidget()
        body = QVBoxLayout(main)
        body.setContentsMargins(28,24,28,24)
        body.setSpacing(16)
        shell.addWidget(main,1)
        self.title = label("Přehled systému","title")
        body.addWidget(self.title)
        self.hardware = label("Detekuji hardware…","muted")
        self.hardware.setWordWrap(True)
        body.addWidget(self.hardware)
        self.stack = QStackedWidget()
        body.addWidget(self.stack,1)
        self.processes = Processes()
        self.recording = Recording()
        self.analysis = Analysis()
        self.gaming = GamingPage(self.monitor, self, self.prefs)
        self.benchmark = BenchmarkPage(self.gaming.fps.capture, lambda: self.navigate(7))
        self.settings_page = SettingsPage(self.prefs, self.reset_preferences,
                                          lambda: self.navigate(7), lambda: self.navigate(5))
        self.recording.interval.setCurrentText(str(self.prefs.get("recording/interval")))
        self.recording.interval.currentTextChanged.connect(self.save_recording_interval)
        self.views = [
            ("Přehled","Přehled systému",self.overview(),"overview"),
            ("Procesor","Procesor",self.cpu_page(),"cpu"),
            ("Disky","Úložiště",self.disk_page(),"disks"),
            ("Síť","Síťový provoz",self.network_page(),"network"),
            ("Procesy","Správce procesů",self.processes,"processes"),
            ("Záznam","Záznam výkonu",self.recording,"recording"),
            ("Analýza","Analýza výkonu",scroll(self.analysis),"analysis"),
            ("Gaming","Gaming Mode & Overlay",scroll(self.gaming),"gaming"),
            ("Benchmark","Gaming Performance Analyzer",scroll(self.benchmark),"benchmark"),
            ("Nastavení","Nastavení aplikace",scroll(self.settings_page),"settings"),
        ]
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i,(name,title,widget,icon) in enumerate(self.views):
            if i == 5:
                nav.addSpacing(10)
                nav.addWidget(label("SESSION","muted"))
            self.stack.addWidget(widget)
            item = button(name)
            item.setObjectName("nav")
            item.setIcon(navigation_icon(icon))
            item.setIconSize(QSize(20, 20))
            item.setCheckable(True)
            self.group.addButton(item,i)
            item.clicked.connect(lambda checked=False,index=i:self.navigate(index))
            nav.addWidget(item)
        nav.addStretch()
        self.live = label("●  Živé měření","muted")
        self.live.setStyleSheet("color: "+GREEN)
        nav.addWidget(self.live)
        nav.addWidget(label("VERSION "+__version__,"muted"))
        last = self.prefs.get("startup/last_page") if self.prefs.get("startup/remember_page") else "Přehled"
        index = next((i for i, view in enumerate(self.views) if view[0] == last), 0)
        self.navigate(index)
        self.restore_window_preferences()
        self.monitor.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def overview(self):
        widget,layout = page()
        row = QHBoxLayout()
        row.setSpacing(14)
        self.metrics = [MetricCard("CPU / PROCESOR",BLUE),MetricCard("RAM / PAMĚŤ",ORANGE),MetricCard("GPU / 3D",GREEN)]
        for item in self.metrics:
            row.addWidget(item,1)
        layout.addLayout(row)
        panel,body = card()
        body.addWidget(label("Historie vytížení","section"))
        body.addWidget(label("Posledních 60 vzorků • CPU / RAM / GPU","muted"))
        self.plot = Plot()
        body.addWidget(self.plot,1)
        layout.addWidget(panel,1)
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
        self.disk_rate = label("N/A","value")
        body.addWidget(self.disk_rate)
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

    def navigate(self,index):
        self.group.button(index).setChecked(True)
        self.stack.setCurrentIndex(index)
        self.monitor.set_process_visible(index == 4 and not self.isMinimized())
        self.prefs.set("startup/last_page", self.views[index][0])
        self.prefs.sync()
        self.title.setText(self.views[index][1])
        if hasattr(self,"timer"):
            self.render_page()

    def refresh(self):
        self.monitor.set_process_visible(self.stack.currentIndex() == 4 and not self.isMinimized())
        self.hardware.setText(self.monitor.hardware)
        basic = self.monitor.basic
        if basic is not None:
            cpu,ram = basic
            gpu = self.monitor.gpu
            self.recording.capture(cpu,ram,gpu,self.monitor.advanced)
            self.history.append((cpu,ram.percent,gpu))
        recording = self.recording.recorder.active
        self.benchmark.refresh(self.stack.currentIndex() == 8 and not self.isMinimized())
        benchmarking = self.gaming.fps.capture.benchmark.active
        self.gaming.refresh(basic, self.monitor.gpu, self.monitor.advanced, recording or benchmarking, not self.isMinimized())
        self.live.setText("●  Benchmark" if benchmarking else "●  Záznam probíhá" if recording else
                          "●  Gaming Mode" if self.gaming.enabled else "●  Živé měření")
        if not self.isMinimized():
            self.render_page()

    def render_page(self):
        index = self.stack.currentIndex()
        basic = self.monitor.basic
        sample = self.monitor.advanced or {}
        if index == 0 and basic is not None:
            cpu,ram = basic
            self.metrics[0].set_value(cpu,f"{psutil.cpu_count(logical=False)} jader / {psutil.cpu_count()} vláken")
            self.metrics[1].set_value(ram.percent,f"{ram.available/1024**3:.2f} / {ram.total/1024**3:.2f} GiB dostupné")
            self.metrics[2].set_value(self.monitor.gpu,"Nejvytíženější 3D jednotka")
            self.plot.render(list(range(1-len(self.history),1)),[(n,c,[r[j] for r in self.history]) for j,(n,c) in enumerate((("CPU",BLUE),("RAM",ORANGE),("GPU",GREEN)))],True,"Vzorky")
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
            self.disk_rate.setText(f"Čtení {rate(read)}   /   Zápis {rate(write)}")
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
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI",10))
    app.setStyleSheet(STYLE)
    window = Window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
