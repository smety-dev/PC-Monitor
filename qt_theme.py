"""Shared Qt visual components."""
from PySide6.QtCore import Qt, QRectF, QByteArray
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QPushButton

BG = "#0a0e17"
PANEL = "#121a28"
TEXT = "#edf2fb"
MUTED = "#98a9c2"
BLUE = "#7c9cff"
GREEN = "#42dbb0"
ORANGE = "#ffc078"
GRID = "#26344a"

STYLE = """
QWidget { background: #0a0e17; color: #edf2fb; font-family: 'Segoe UI'; font-size: 13px; }
QFrame#sidebar { background: #101624; border-right: 1px solid #202c40; }
QFrame#card { background: #121a28; border: 1px solid #253249; border-radius: 14px; }
QFrame#card QLabel, QFrame#sidebar QLabel { background: transparent; }
QLabel[role="muted"] { color: #98a9c2; }
QLabel[role="title"] { font-size: 28px; font-weight: 700; }
QLabel[role="section"] { font-size: 16px; font-weight: 600; }
QLabel[role="value"] { font-size: 29px; font-weight: 700; }
QPushButton { background: #24334b; border: 0; border-radius: 8px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #344761; }
QPushButton:disabled { color: #718097; background: #192334; }
QPushButton#primary { background: #7c9cff; color: #0a0e17; }
QPushButton#primary:hover { background: #9bb2ff; }
QPushButton#primary:disabled { background: #27334b; color: #718097; }
QPushButton#nav { text-align: left; background: transparent; color: #98a9c2; padding: 12px 15px; }
QPushButton#nav:hover { background: #1c293e; color: #edf2fb; }
QPushButton#nav:checked { background: #263656; color: #a9bdff; }
QLineEdit, QComboBox { background: #151e2d; border: 1px solid #2c3c55; border-radius: 8px; padding: 9px; selection-background-color: #385384; }
QComboBox QAbstractItemView { background: #151e2d; selection-background-color: #385384; color: #edf2fb; }
QTableWidget { background: #121a28; alternate-background-color: #172233; border: 1px solid #253249; border-radius: 8px; gridline-color: #253249; selection-background-color: #304872; }
QHeaderView::section { background: #1c293d; color: #aabbd4; padding: 10px; border: 0; font-weight: 600; }
QScrollArea { border: 0; }
QScrollBar:vertical { background: #101624; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #34445e; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QCheckBox { spacing: 9px; background: transparent; padding: 3px 0; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #405576; border-radius: 4px; background: #192334; }
QCheckBox::indicator:checked { background: #7c9cff; border: 2px solid #a9bdff; }
QSlider::groove:horizontal { height: 6px; background: #26344a; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #7c9cff; border-radius: 3px; }
QSlider::handle:horizontal { background: #edf2fb; width: 16px; margin: -5px 0; border-radius: 8px; }
QProgressBar { background: #26344a; border: 0; border-radius: 5px; min-height: 10px; max-height: 10px; }
QProgressBar::chunk { background: #7c9cff; border-radius: 5px; }
"""


# Original outline icons, drawn on a consistent 24 × 24 grid.
NAV_ICONS = {
    "overview": '<rect x="3" y="3" width="7" height="7" rx="1.3"/><rect x="14" y="3" width="7" height="7" rx="1.3"/><rect x="3" y="14" width="7" height="7" rx="1.3"/><rect x="14" y="14" width="7" height="7" rx="1.3"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx=".7"/><path d="M9 3v3m6-3v3M9 18v3m6-3v3M3 9h3m-3 6h3m12-6h3m-3 6h3"/>',
    "disks": '<path d="M3 13l3-8h12l3 8"/><rect x="3" y="13" width="18" height="6" rx="1.8"/><path d="M7 16h.1M11 16h.1M15 16h3"/>',
    "network": '<rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-4h12v4"/>',
    "processes": '<path d="M4 5h2m3 0h11M4 12h2m3 0h11M4 19h2m3 0h11"/>',
    "recording": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="12" cy="12" r="4"/>',
    "analysis": '<path d="M4 4v16h16M7 15l4-5 4 2 5-6"/><circle cx="20" cy="6" r=".6"/>',
    "gaming": '<path d="M8 7h8c3 0 4.4 2.5 5.1 5.8l.6 3.1c.5 2.7-2 4-3.6 2.4L15 15H9l-3.1 3.3c-1.6 1.6-4.1.3-3.6-2.4l.6-3.1C3.6 9.5 5 7 8 7Z"/><path d="M6.5 11h4m-2-2v4m7.5-2h.1m2.4 2h.1"/>',
    "benchmark": '<path d="M4 18a9 9 0 1 1 16 0M12 6v2M6.5 9.5l1.4 1.4M17.5 9.5l-1.4 1.4M12 15l4-5M8 19h8"/><circle cx="12" cy="15" r="1.2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M9.4 3.5h5.2l.7 2.7 2.4 1.4 2.7-.7 2.1 3.6-2 2v2.8l2 2-2.1 3.6-2.7-.7-2.4 1.4-.7 2.7h-5.2l-.7-2.7-2.4-1.4-2.7.7-2.1-3.6 2-2v-2.8l-2-2 2.1-3.6 2.7.7 2.4-1.4z" transform="translate(1 0) scale(.92)"/>',
}


def navigation_icon(name):
    """Render sharp, theme-aware icons for normal and selected button states."""
    icon = QIcon()
    for state, color in ((QIcon.State.Off, MUTED), (QIcon.State.On, "#a9bdff")):
        for mode, tint in ((QIcon.Mode.Normal, color), (QIcon.Mode.Active, TEXT if state == QIcon.State.Off else color)):
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
                   f'fill="none" stroke="{tint}" stroke-width="1.7" '
                   f'stroke-linecap="round" stroke-linejoin="round">{NAV_ICONS[name]}</svg>')
            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
            for scale in (1, 2, 3):
                size = 20 * scale
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter, QRectF(0, 0, size, size))
                painter.end()
                pixmap.setDevicePixelRatio(scale)
                icon.addPixmap(pixmap, mode, state)
    return icon


def label(text="", role=None):
    obj = QLabel(text)
    obj.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        obj.setProperty("role", role)
    return obj


def card():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 16, 20, 16)
    layout.setSpacing(10)
    return frame, layout


def button(text, primary=False):
    obj = QPushButton(text)
    obj.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        obj.setObjectName("primary")
    return obj


class Ring(QWidget):
    def __init__(self, color):
        super().__init__()
        self.color = color
        self.value = None
        self.setMinimumHeight(122)

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width()-24, self.height()-20)
        if size <= 0:
            return
        rect = QRectF((self.width()-size)/2, (self.height()-size)/2, size, size)
        pen = QPen(QColor(GRID), 9)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 225*16, -270*16)
        if self.value is not None:
            pen.setColor(QColor(self.color))
            p.setPen(pen)
            p.drawArc(rect, 225*16, -int(270*16*max(0,min(100,self.value))/100))
        p.setPen(QColor(TEXT))
        p.setFont(QFont("Segoe UI", 22, QFont.Weight.DemiBold))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                   "N/A" if self.value is None else f"{self.value:.1f}%")


class MetricCard(QFrame):
    def __init__(self, name, color):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.addWidget(label(name, "section"))
        self.ring = Ring(color)
        layout.addWidget(self.ring)
        self.detail = label("Čekám na data", "muted")
        layout.addWidget(self.detail)

    def set_value(self, value, detail):
        self.ring.set_value(value)
        self.detail.setText(detail)
