"""PC Monitor Qt desktop application."""
import sys
from collections import deque
import psutil
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedWidget, QButtonGroup, QScrollArea, QProgressBar,
    QStyle)
from qt_theme import STYLE, BLUE, GREEN, ORANGE, MetricCard, card, label, button
from qt_monitor import Monitor
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
        nav.setSpacing(8)
        nav.addWidget(label("PC Monitor","section"))
        nav.addWidget(label("PERFORMANCE STUDIO","muted"))
        nav.addSpacing(26)
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
        self.views = [
            ("Přehled","Přehled systému",self.overview(),QStyle.StandardPixmap.SP_ComputerIcon),
            ("Procesor","Procesor",self.cpu_page(),QStyle.StandardPixmap.SP_DriveHDIcon),
            ("Disky","Úložiště",self.disk_page(),QStyle.StandardPixmap.SP_DriveHDIcon),
            ("Síť","Síťový provoz",self.network_page(),QStyle.StandardPixmap.SP_DriveNetIcon),
            ("Procesy","Správce procesů",self.processes,QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("Záznam","Záznam výkonu",self.recording,QStyle.StandardPixmap.SP_DialogSaveButton),
            ("Analýza","Analýza výkonu",scroll(self.analysis),QStyle.StandardPixmap.SP_FileDialogContentsView),
        ]
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i,(name,title,widget,icon) in enumerate(self.views):
            if i == 5:
                nav.addSpacing(20)
                nav.addWidget(label("SESSION","muted"))
            self.stack.addWidget(widget)
            item = button(name)
            item.setObjectName("nav")
            item.setIcon(self.style().standardIcon(icon))
            item.setCheckable(True)
            self.group.addButton(item,i)
            item.clicked.connect(lambda checked=False,index=i:self.navigate(index))
            nav.addWidget(item)
        nav.addStretch()
        self.live = label("●  Živé měření","muted")
        self.live.setStyleSheet("color: "+GREEN)
        nav.addWidget(self.live)
        nav.addWidget(label("VERSION "+__version__,"muted"))
        self.group.button(0).setChecked(True)
        self.navigate(0)
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

    def navigate(self,index):
        self.stack.setCurrentIndex(index)
        self.title.setText(self.views[index][1])
        if hasattr(self,"timer"):
            self.render_page()

    def refresh(self):
        self.hardware.setText(self.monitor.hardware)
        basic = self.monitor.basic
        if basic is not None:
            cpu,ram = basic
            gpu = self.monitor.gpu
            self.recording.capture(cpu,ram,gpu,self.monitor.advanced)
            self.history.append((cpu,ram.percent,gpu))
        self.live.setText("●  Záznam probíhá" if self.recording.recorder.active else "●  Živé měření")
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
            self.processes.refresh(self.monitor.processes)

    def closeEvent(self,event):
        self.timer.stop()
        self.monitor.close()
        self.recording.finish()
        self.analysis.shutdown()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI",10))
    app.setStyleSheet(STYLE)
    window = Window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
