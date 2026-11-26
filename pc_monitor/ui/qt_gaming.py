"""Standalone, non-injecting desktop overlay and gaming settings."""
from pc_monitor.locales.i18n import tr
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSlider, QCheckBox
from pc_monitor.gaming.gaming_metrics import CORNERS, percent, fraction, frequency, available_memory, overlay_position
from pc_monitor.ui.qt_fps import FpsPanel
from pc_monitor.ui.qt_theme import BLUE, GREEN, ORANGE, TEXT, MUTED, GRID, PANEL, DANGER, SPACE, card, label, button, make_font, workspace_tabs, workspace_tab


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
        self.frame_stats = None
        self.show_fps = True

    def configure(self, alpha, detailed, show_fps):
        self.alpha = round(alpha * 255 / 100)
        self.detailed = detailed
        self.show_fps = show_fps
        self.setFixedSize(310, (166 if detailed else 140) + (56 if show_fps else 0))
        self.update()

    def set_metrics(self, basic, gpu, advanced, recording, frame_stats):
        if basic is None:
            cpu, ram_percent, self.memory = None, None, None
        else:
            cpu, ram = basic
            ram_percent, self.memory = ram.percent, ram.available
        self.values = (cpu, gpu, ram_percent)
        self.freq = (advanced or {}).get("frequency")
        self.recording = recording
        self.frame_stats = frame_stats
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(GRID))
        background = QColor(PANEL)
        background.setAlpha(self.alpha)
        p.setBrush(background)
        p.drawRoundedRect(QRectF(1, 1, self.width()-2, self.height()-2), 12, 12)
        p.setFont(make_font(13, QFont.Weight.DemiBold))
        p.setPen(QColor(MUTED))
        p.drawText(QRectF(15, 9, 180, 19), Qt.AlignmentFlag.AlignVCenter, "PC MONITOR  /  LIVE")
        p.setPen(QColor(DANGER if self.recording else GREEN))
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
        if self.show_fps:
            stats = self.frame_stats
            y = 166 if self.detailed else 140
            p.setPen(QColor(GRID))
            p.drawLine(15, y-3, 295, y-3)
            p.setFont(make_font(22, QFont.Weight.DemiBold))
            p.setPen(QColor(GREEN))
            p.drawText(QRectF(15, y+3, 125, 25), Qt.AlignmentFlag.AlignVCenter,
                       f"{stats.fps:.0f} FPS" if stats else "— FPS")
            p.setFont(make_font(12))
            p.setPen(QColor(MUTED))
            low = f"{stats.low:.0f}" if stats and stats.low is not None else "—"
            ms = f"{stats.frametime:.1f}" if stats else "—"
            p.drawText(QRectF(15, y+30, 280, 19), Qt.AlignmentFlag.AlignVCenter,
                       f"1% low  {low} FPS   ·   {ms} ms")
        if self.detailed:
            p.setPen(QColor(MUTED))
            p.setFont(make_font(11))
            p.drawText(QRectF(15, 136, 280, 19), Qt.AlignmentFlag.AlignVCenter,
                       frequency(self.freq) + "   ·   " + tr(available_memory(self.memory)))


class GamingPage(QWidget):
    def __init__(self, monitor, parent_window, prefs):
        super().__init__()
        self.monitor = monitor
        self.prefs = prefs
        self.loading_preferences = True
        self.overlay = Overlay()
        self.preview = Overlay(preview=True)
        self.enabled = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.tabs = workspace_tabs(layout)
        fps_layout = workspace_tab(self.tabs, tr("Měření FPS"))
        self.fps = FpsPanel()
        fps_layout.addWidget(self.fps)
        fps_layout.addStretch()
        layout = workspace_tab(self.tabs, tr("Herní overlay"))

        panel, body = card()
        header = QHBoxLayout()
        header.addWidget(label(tr("Zobrazení výkonu ve hře"), "section"))
        header.addStretch()
        self.status = label(tr("VYPNUTO"), "muted")
        header.addWidget(self.status)
        body.addLayout(header)
        description = label(tr("Při hraní zobrazí živé údaje v samostatném overlayi. Kliknutí procházejí do hry."), "muted")
        description.setWordWrap(True)
        body.addWidget(description)
        controls = QHBoxLayout()
        self.toggle = button(tr("Zapnout overlay"), True)
        self.toggle.clicked.connect(self.toggle_mode)
        controls.addWidget(self.toggle)
        self.minimize = button(tr("Minimalizovat aplikaci"))
        self.minimize.clicked.connect(parent_window.showMinimized)
        controls.addWidget(self.minimize)
        controls.addStretch()
        body.addLayout(controls)
        self.low_overhead = QCheckBox(tr("Pozastavit sběr seznamu procesů během Gaming Mode"))
        self.low_overhead.setChecked(True)
        self.low_overhead.toggled.connect(self.apply_mode)
        body.addWidget(self.low_overhead)
        layout.addWidget(panel)

        panel, body = card()
        body.addWidget(label(tr("Nastavení overlaye"), "section"))
        row = QHBoxLayout()
        row.addWidget(label("Monitor", "muted"))
        self.screen = QComboBox()
        row.addWidget(self.screen, 1)
        row.addWidget(label(tr("Umístění"), "muted"))
        self.corner = QComboBox()
        for corner in CORNERS:
            self.corner.addItem(tr(corner), corner)
        self.corner.setCurrentIndex(1)
        row.addWidget(self.corner, 1)
        body.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(label(tr("Neprůhlednost pozadí"), "muted"))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(35, 100)
        self.opacity.setValue(90)
        row.addWidget(self.opacity, 1)
        self.opacity_text = label("90 %")
        row.addWidget(self.opacity_text)
        body.addLayout(row)
        self.details = QCheckBox(tr("Zobrazit frekvenci CPU a dostupnou RAM"))
        self.details.setChecked(True)
        body.addWidget(self.details)
        self.fps_visible = QCheckBox(tr("Zobrazit FPS, 1% Low a frametime"))
        self.fps_visible.setChecked(True)
        body.addWidget(self.fps_visible)
        layout.addWidget(panel)

        panel, body = card()
        body.addWidget(label(tr("Živý náhled"), "section"))
        body.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignLeft)
        hint = label(tr("Pro hry použij režim bez okrajů nebo v okně. V exkluzivním fullscreenu nemusí být overlay viditelný. FPS vyžaduje samostatné měření PresentMon. Teploty zatím neměříme."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        layout.addWidget(panel)
        layout.addStretch()

        self.screen.currentIndexChanged.connect(self.apply_settings)
        self.corner.currentIndexChanged.connect(self.apply_settings)
        self.opacity.valueChanged.connect(self.apply_settings)
        self.details.toggled.connect(self.apply_settings)
        self.fps_visible.toggled.connect(self.apply_settings)
        app = QGuiApplication.instance()
        app.screenAdded.connect(self.refresh_screens)
        app.screenRemoved.connect(self.refresh_screens)
        self.refresh_screens()
        self.load_preferences()
        self.screen.currentIndexChanged.connect(self.save_monitor)

    def load_preferences(self):
        self.loading_preferences = True
        self.corner.setCurrentIndex(self.corner.findData(self.prefs.get("overlay/corner")))
        self.opacity.setValue(self.prefs.get("overlay/opacity"))
        self.details.setChecked(self.prefs.get("overlay/details"))
        self.fps_visible.setChecked(self.prefs.get("overlay/fps"))
        self.low_overhead.setChecked(self.prefs.get("gaming/low_overhead"))
        self.refresh_screens()
        self.loading_preferences = False
        self.apply_settings()
        self.apply_mode()

    def save_monitor(self, *_):
        if not self.loading_preferences:
            self.prefs.set("overlay/monitor", self.screen.currentData() or "")
            self.prefs.sync()

    def refresh_screens(self, *_):
        previous = self.prefs.get("overlay/monitor")
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
                                    (self.overlay.width(), self.overlay.height()), self.corner.currentData())
            if self.overlay.x() != x or self.overlay.y() != y:
                self.overlay.move(x, y)

    def apply_settings(self, *_):
        value = self.opacity.value()
        self.opacity_text.setText(f"{value} %")
        for overlay in (self.overlay, self.preview):
            overlay.configure(value, self.details.isChecked(), self.fps_visible.isChecked())
        self.position_overlay()
        if not self.loading_preferences:
            self.prefs.set("overlay/corner", self.corner.currentData())
            self.prefs.set("overlay/opacity", value)
            self.prefs.set("overlay/details", self.details.isChecked())
            self.prefs.set("overlay/fps", self.fps_visible.isChecked())
            self.prefs.sync()

    def toggle_mode(self):
        self.enabled = not self.enabled
        self.apply_mode()

    def apply_mode(self, *_):
        if not self.loading_preferences:
            self.prefs.set("gaming/low_overhead", self.low_overhead.isChecked())
            self.prefs.sync()
        self.monitor.set_gaming(self.enabled and self.low_overhead.isChecked())
        self.toggle.setText(tr("Vypnout overlay") if self.enabled else tr("Zapnout overlay"))
        self.status.setText(tr("AKTIVNÍ") if self.enabled else tr("VYPNUTO"))
        self.status.setStyleSheet("color: " + (GREEN if self.enabled else MUTED))
        if self.enabled:
            self.position_overlay()
            self.overlay.show()
        else:
            self.overlay.hide()

    def refresh(self, basic, gpu, advanced, recording, window_visible=True):
        visible = window_visible and self.isVisible()
        fps_visible = visible and self.tabs.currentIndex() == 0
        preview_visible = visible and self.tabs.currentIndex() == 1
        stats = self.fps.refresh(fps_visible, fps_visible or ((self.enabled or preview_visible) and self.fps_visible.isChecked()))
        if preview_visible:
            self.preview.set_metrics(basic, gpu, advanced, recording, stats)
        if self.enabled:
            self.position_overlay()
            self.overlay.set_metrics(basic, gpu, advanced, recording, stats)

    def shutdown(self):
        self.enabled = False
        self.overlay.close()
        self.fps.shutdown()
        self.monitor.set_gaming(False)
