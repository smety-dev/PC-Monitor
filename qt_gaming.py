"""Standalone, non-injecting desktop overlay and gaming settings."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QCheckBox
from gaming_metrics import CORNERS, percent, fraction, frequency, available_memory, overlay_position
from qt_theme import BLUE, GREEN, ORANGE, TEXT, MUTED, GRID, card, label, button


class Overlay(QWidget):
    def __init__(self, preview=False):
        flags = (Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool |
                 Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowTransparentForInput |
                 Qt.WindowType.WindowDoesNotAcceptFocus)
        super().__init__(None, flags if not preview else Qt.WindowType.Widget)
        if not preview:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(310, 166)
        self.values = (None, None, None)
        self.freq = None
        self.memory = None
        self.recording = False
        self.alpha = 230
        self.detailed = True

    def configure(self, alpha, detailed):
        self.alpha = round(alpha * 255 / 100)
        self.detailed = detailed
        self.setFixedSize(310, 166 if detailed else 140)
        self.update()

    def set_metrics(self, basic, gpu, advanced, recording):
        if basic is None:
            cpu, ram_percent, self.memory = None, None, None
        else:
            cpu, ram = basic
            ram_percent, self.memory = ram.percent, ram.available
        self.values = (cpu, gpu, ram_percent)
        self.freq = (advanced or {}).get("frequency")
        self.recording = recording
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(GRID))
        p.setBrush(QColor(12, 19, 32, self.alpha))
        p.drawRoundedRect(QRectF(1, 1, self.width()-2, self.height()-2), 12, 12)
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        p.setPen(QColor(MUTED))
        p.drawText(QRectF(15, 9, 180, 19), Qt.AlignmentFlag.AlignVCenter, "PC MONITOR  /  LIVE")
        p.setPen(QColor("#ff788c" if self.recording else GREEN))
        p.drawText(QRectF(197, 9, 98, 19), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   "● REC" if self.recording else "● LIVE")
        for i, (name, color, value) in enumerate(zip(("CPU", "GPU 3D", "RAM"), (BLUE, GREEN, ORANGE), self.values)):
            y = 34 + i*32
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(15, y, 65, 18), Qt.AlignmentFlag.AlignVCenter, name)
            p.setPen(QColor(TEXT))
            p.drawText(QRectF(218, y, 77, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, percent(value))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(GRID))
            p.drawRoundedRect(QRectF(85, y+6, 123, 6), 3, 3)
            width = 123 * fraction(value)
            if width > 0:
                p.setBrush(QColor(color))
                p.drawRoundedRect(QRectF(85, y+6, width, 6), 3, 3)
        if self.detailed:
            p.setPen(QColor(MUTED))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(15, 136, 280, 19), Qt.AlignmentFlag.AlignVCenter,
                       frequency(self.freq) + "   ·   " + available_memory(self.memory))


class GamingPage(QWidget):
    def __init__(self, monitor, parent_window):
        super().__init__()
        self.monitor = monitor
        self.window = parent_window
        self.overlay = Overlay()
        self.preview = Overlay(preview=True)
        self.enabled = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        panel, body = card()
        header = QHBoxLayout()
        header.addWidget(label("Gaming Mode", "section"))
        header.addStretch()
        self.status = label("VYPNUTO", "muted")
        header.addWidget(self.status)
        body.addLayout(header)
        description = label("Při hraní zobrazí živé údaje v samostatném overlayi. Kliknutí procházejí do hry.", "muted")
        description.setWordWrap(True)
        body.addWidget(description)
        controls = QHBoxLayout()
        self.toggle = button("Zapnout Gaming Mode", True)
        self.toggle.clicked.connect(self.toggle_mode)
        controls.addWidget(self.toggle)
        self.minimize = button("Minimalizovat aplikaci")
        self.minimize.clicked.connect(parent_window.showMinimized)
        controls.addWidget(self.minimize)
        controls.addStretch()
        body.addLayout(controls)
        self.low_overhead = QCheckBox("Pozastavit sběr seznamu procesů během Gaming Mode")
        self.low_overhead.setChecked(True)
        self.low_overhead.toggled.connect(self.apply_mode)
        body.addWidget(self.low_overhead)
        layout.addWidget(panel)

        panel, body = card()
        body.addWidget(label("Nastavení overlaye", "section"))
        row = QHBoxLayout()
        row.addWidget(label("Monitor", "muted"))
        self.screen = QComboBox()
        row.addWidget(self.screen, 1)
        row.addWidget(label("Umístění", "muted"))
        self.corner = QComboBox()
        self.corner.addItems(CORNERS)
        self.corner.setCurrentIndex(1)
        row.addWidget(self.corner, 1)
        body.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(label("Neprůhlednost pozadí", "muted"))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(35, 100)
        self.opacity.setValue(90)
        row.addWidget(self.opacity, 1)
        self.opacity_text = label("90 %")
        row.addWidget(self.opacity_text)
        body.addLayout(row)
        self.details = QCheckBox("Zobrazit frekvenci CPU a dostupnou RAM")
        self.details.setChecked(True)
        body.addWidget(self.details)
        layout.addWidget(panel)

        panel, body = card()
        body.addWidget(label("Živý náhled", "section"))
        body.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignLeft)
        hint = label("Pro hry použij režim bez okrajů nebo v okně. V exkluzivním fullscreenu nemusí být overlay viditelný. FPS a teploty zatím neměříme.", "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        layout.addWidget(panel)
        layout.addStretch()

        self.screen.currentIndexChanged.connect(self.apply_settings)
        self.corner.currentIndexChanged.connect(self.apply_settings)
        self.opacity.valueChanged.connect(self.apply_settings)
        self.details.toggled.connect(self.apply_settings)
        app = QGuiApplication.instance()
        app.screenAdded.connect(self.refresh_screens)
        app.screenRemoved.connect(self.refresh_screens)
        self.refresh_screens()

    def refresh_screens(self, *_):
        previous = self.screen.currentData()
        self.screen.blockSignals(True)
        self.screen.clear()
        for screen in QGuiApplication.screens():
            g = screen.geometry()
            self.screen.addItem(f"{screen.name()} · {g.width()} × {g.height()}", screen.name())
        index = self.screen.findData(previous)
        if index < 0 and QGuiApplication.primaryScreen():
            index = self.screen.findData(QGuiApplication.primaryScreen().name())
        self.screen.setCurrentIndex(max(0, index))
        self.screen.blockSignals(False)
        self.apply_settings()

    def selected_screen(self):
        name = self.screen.currentData()
        return next((s for s in QGuiApplication.screens() if s.name() == name),
                    QGuiApplication.primaryScreen())

    def position_overlay(self):
        screen = self.selected_screen()
        if screen:
            g = screen.geometry()
            x, y = overlay_position((g.x(), g.y(), g.width(), g.height()),
                                    (self.overlay.width(), self.overlay.height()), self.corner.currentText())
            self.overlay.move(x, y)

    def apply_settings(self, *_):
        value = self.opacity.value()
        self.opacity_text.setText(f"{value} %")
        for overlay in (self.overlay, self.preview):
            overlay.configure(value, self.details.isChecked())
        self.position_overlay()

    def toggle_mode(self):
        self.enabled = not self.enabled
        self.apply_mode()

    def apply_mode(self, *_):
        self.monitor.set_gaming(self.enabled and self.low_overhead.isChecked())
        self.toggle.setText("Vypnout Gaming Mode" if self.enabled else "Zapnout Gaming Mode")
        self.status.setText("AKTIVNÍ" if self.enabled else "VYPNUTO")
        self.status.setStyleSheet("color: " + (GREEN if self.enabled else MUTED))
        if self.enabled:
            self.position_overlay()
            self.overlay.show()
        else:
            self.overlay.hide()

    def refresh(self, basic, gpu, advanced, recording):
        if self.isVisible():
            self.preview.set_metrics(basic, gpu, advanced, recording)
        if self.enabled:
            self.position_overlay()
            self.overlay.set_metrics(basic, gpu, advanced, recording)

    def shutdown(self):
        self.enabled = False
        self.overlay.close()
        self.monitor.set_gaming(False)
