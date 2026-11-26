"""Shared Qt visual components."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
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
QProgressBar { background: #26344a; border: 0; border-radius: 5px; min-height: 10px; max-height: 10px; }
QProgressBar::chunk { background: #7c9cff; border-radius: 5px; }
"""


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
