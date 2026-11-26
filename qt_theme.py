"""Shared Qt visual components."""
from PySide6.QtCore import Qt, QRectF, QByteArray
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QFontDatabase, QIcon, QPixmap, QPalette
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QTabWidget, QScrollArea
from string import Template

# Shared color, typography and spacing tokens. Metric hues are semantic, not navigation hues.
BG = "#0d1117"
PANEL = "#161c25"
SIDEBAR = "#10151d"
SURFACE = "#1b2430"
RAISED = "#222d3b"
BORDER = "#2b3747"
GRID = "#293544"
TEXT = "#edf2fb"
MUTED = "#aebdd0"
SUBTLE = "#91a1b7"
BLUE = "#83a8ff"
GREEN = "#45dcb5"
ORANGE = "#ffc078"
DANGER = "#ff8395"
NAV_TINT = "#a9bad4"
NAV_SELECTED = "#243650"
NAV_TEXT = "#d9e6ff"
DISABLED = "#718097"
SPACE = 8
CARD_RADIUS = 12

STYLE = Template("""
QWidget { color: $TEXT; font-size: 14px; }
QWidget#workspace { background: $BG; }
QLabel[role="subtitle"] { font-size: 13px; color: $MUTED; }
QLabel[role="stat"] { font-size: 34px; font-weight: 600; }
QLabel[role="unit"] { font-size: 15px; color: $MUTED; font-weight: 500; }
QLabel[role="status"] { font-size: 12px; font-weight: 600; }
QFrame#divider { background: $BORDER; max-height: 1px; border: 0; }
QMainWindow, QDialog, QStackedWidget { background: $BG; }
QFrame#sidebar { background: $SIDEBAR; border-right: 1px solid $BORDER; }
QWidget#navContent, QScrollArea#navScroll, QWidget#navViewport { background: $SIDEBAR; }
QFrame#card { background: $PANEL; border: 1px solid $BORDER; border-radius: ${CARD_RADIUS}px; }
QFrame#card QLabel, QFrame#sidebar QLabel { background: transparent; }
QLabel[role="muted"] { color: $MUTED; font-size: 13px; }
QLabel[role="eyebrow"] { color: $SUBTLE; font-size: 11px; font-weight: 600; }
QLabel[role="brand"] { font-size: 21px; font-weight: 700; color: $TEXT; }
QLabel[role="title"] { font-size: 28px; font-weight: 600; }
QLabel[role="section"] { font-size: 16px; font-weight: 600; }
QLabel[role="value"] { font-size: 28px; font-weight: 600; }
QLabel[role="metric"] { color: $MUTED; font-size: 12px; font-weight: 600; }
QPushButton { background: $RAISED; border: 1px solid $BORDER; border-radius: 9px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #2b3d56; }
QPushButton:pressed { background: $SURFACE; }
QPushButton:focus { border-color: $BLUE; }
QPushButton:disabled { color: $DISABLED; background: $SURFACE; border-color: $BORDER; }
QPushButton#primary { background: $BLUE; border-color: $BLUE; color: $BG; }
QPushButton#primary:hover { background: #a4beff; }
QPushButton#primary:pressed { background: #6f97ed; }
QPushButton#primary:focus { border-color: $TEXT; }
QPushButton#primary:disabled { background: $RAISED; border-color: $BORDER; color: $DISABLED; }
QPushButton#nav { text-align: left; background: transparent; color: $MUTED; border: 1px solid transparent; border-radius: 10px; padding: 8px 12px; font-weight: 500; }
QPushButton#nav:hover { background: $SURFACE; color: $TEXT; }
QPushButton#nav:checked { background: $NAV_SELECTED; color: $NAV_TEXT; border-color: #344b6c; font-weight: 600; }
QPushButton#nav:focus { border-color: $BLUE; }
QLineEdit, QComboBox, QPlainTextEdit { background: $SURFACE; border: 1px solid $BORDER; border-radius: 9px; padding: 8px; selection-background-color: $NAV_SELECTED; }
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus { border-color: $BLUE; }
QLineEdit:disabled, QComboBox:disabled { color: $DISABLED; }
QComboBox QAbstractItemView { background: $SURFACE; selection-background-color: $NAV_SELECTED; color: $TEXT; outline: 0; padding: 3px; }
QTableWidget { background: $PANEL; alternate-background-color: $SURFACE; border: 1px solid $BORDER; border-radius: 10px; gridline-color: $GRID; selection-background-color: $NAV_SELECTED; selection-color: $TEXT; outline: 0; }
QTableWidget::item { padding: 5px 8px; }
QTableWidget::item:selected { background: $NAV_SELECTED; color: $TEXT; }
QHeaderView { background: $RAISED; }
QHeaderView::section { background: $RAISED; color: $NAV_TEXT; padding: 9px; border: 0; border-bottom: 1px solid $BORDER; font-size: 12px; font-weight: 600; }
QHeaderView::section:hover { background: #2b3d56; color: $TEXT; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #3a4b64; min-height: 24px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #3a4b64; min-width: 24px; border-radius: 4px; }
QScrollBar::handle:hover { background: #536984; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QCheckBox { spacing: 10px; background: transparent; padding: 4px 0; }
QCheckBox:disabled { color: $DISABLED; }
QSlider::groove:horizontal { height: 6px; background: $GRID; border-radius: 3px; }
QSlider::sub-page:horizontal { background: $BLUE; border-radius: 3px; }
QSlider::handle:horizontal { background: $TEXT; width: 16px; margin: -5px 0; border-radius: 8px; }
QProgressBar { background: $GRID; border: 0; border-radius: 5px; min-height: 10px; max-height: 10px; }
QProgressBar::chunk { background: $BLUE; border-radius: 5px; }
QTabWidget::pane { border: 0; background: $BG; top: 0px; }
QTabBar::tab { background: transparent; color: $MUTED; border: 0; border-bottom: 2px solid transparent; padding: 10px 18px; font-weight: 500; }
QTabBar::tab:hover { color: $TEXT; background: $SURFACE; }
QTabBar::tab:selected { color: $TEXT; border-bottom: 2px solid $BLUE; font-weight: 600; }
QTabBar::tab:focus { background: $SURFACE; }
QProgressBar#metricBar { min-height: 6px; max-height: 6px; border-radius: 3px; }
QProgressBar#metricBar::chunk { border-radius: 3px; }
QToolTip { background: $RAISED; color: $TEXT; border: 1px solid $BORDER; padding: 6px; }
""").substitute(globals())


def preferred_font(families=None):
    """Resolve installed fonts only after QApplication exists."""
    available = {name.casefold(): name for name in
                 (QFontDatabase.families() if families is None else families)}
    for name in ("Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", "Inter", "Noto Sans", "Arial", "DejaVu Sans"):
        if name.casefold() in available:
            return available[name.casefold()]
    return "Sans Serif"


def make_font(size, weight=QFont.Weight.Normal):
    font = QFont(QApplication.font())
    font.setPixelSize(size)
    font.setWeight(weight)
    return font


def configure_theme(app):
    app.setStyle("Fusion")
    family = preferred_font()
    font = QFont(family)
    font.setPixelSize(14)
    app.setFont(font)
    palette = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, BG), (QPalette.ColorRole.WindowText, TEXT),
        (QPalette.ColorRole.Base, PANEL), (QPalette.ColorRole.AlternateBase, SURFACE),
        (QPalette.ColorRole.Text, TEXT), (QPalette.ColorRole.Button, RAISED),
        (QPalette.ColorRole.ButtonText, TEXT), (QPalette.ColorRole.Highlight, BLUE),
        (QPalette.ColorRole.HighlightedText, BG), (QPalette.ColorRole.PlaceholderText, MUTED),
        (QPalette.ColorRole.ToolTipBase, RAISED), (QPalette.ColorRole.ToolTipText, TEXT),
        (QPalette.ColorRole.Link, BLUE)):
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(DISABLED))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)
    return family


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
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M10 3h4l.6 2.5 2 .9 2.2-1.3 2 3.5-1.9 1.8v2.2l1.9 1.8-2 3.5-2.2-1.3-2 .9-.6 2.5h-4l-.6-2.5-2-.9-2.2 1.3-2-3.5 1.9-1.8v-2.2L3.2 8.6l2-3.5 2.2 1.3 2-.9z"/>',
}


def navigation_icon(name):
    """Use exactly one tint for every icon in every Qt mode and state."""
    icon = QIcon()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
           f'fill="none" stroke="{NAV_TINT}" stroke-width="1.75" '
           f'stroke-linecap="round" stroke-linejoin="round">{NAV_ICONS[name]}</svg>')
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    for scale in (1, 2, 3):
        size = 20 * scale
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        pixmap.setDevicePixelRatio(scale)
        for mode in (QIcon.Mode.Normal, QIcon.Mode.Active, QIcon.Mode.Selected, QIcon.Mode.Disabled):
            for state in (QIcon.State.Off, QIcon.State.On):
                icon.addPixmap(pixmap, mode, state)
    return icon


def label(text="", role=None):
    obj = QLabel(text)
    obj.setTextFormat(Qt.TextFormat.PlainText)
    if role:
        obj.setProperty("role", role)
    return obj


def workspace_tab(tabs, title):
    """One independently scrolling workspace; tabs remain visible when scrolling."""
    page = QWidget()
    page.setObjectName("workspace")
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 16, 8, 0)
    layout.setSpacing(2 * SPACE)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    area.setWidget(page)
    tabs.addTab(area, title)
    return layout


def workspace_tabs(parent_layout):
    tabs = QTabWidget()
    tabs.setDocumentMode(True)
    tabs.setElideMode(Qt.TextElideMode.ElideRight)
    parent_layout.addWidget(tabs, 1)
    return tabs


def card():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(2 * SPACE, 2 * SPACE, 2 * SPACE, 2 * SPACE)
    layout.setSpacing(SPACE)
    return frame, layout


def button(text, primary=False):
    obj = QPushButton(text)
    obj.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        obj.setObjectName("primary")
    return obj


class MetricCard(QFrame):
    """Large value and compact utilization bar; no animated gauges."""
    def __init__(self, name, color, unit="%", show_bar=True):
        super().__init__()
        self.setObjectName("card")
        self.color = color
        self.unit = unit
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.addWidget(label(name, "metric"))
        header.addStretch()
        layout.addLayout(header)
        reading = QHBoxLayout()
        reading.setSpacing(5)
        self.value = label("—", "stat")
        self.unit_label = label(unit, "unit")
        reading.addWidget(self.value)
        reading.addWidget(self.unit_label, 0, Qt.AlignmentFlag.AlignBottom)
        reading.addStretch()
        layout.addLayout(reading)
        self.bar = QProgressBar()
        self.bar.setObjectName("metricBar")
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        self.bar.setStyleSheet("QProgressBar::chunk { background: " + color + "; }")
        layout.addWidget(self.bar)
        self.bar.setHidden(not show_bar)
        self.detail = label("Čekám na data", "muted")
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        layout.addStretch()

    def set_value(self, value, detail):
        text = "—" if value is None else f"{value:.1f}".replace(".", ",")
        if self.value.text() != text:
            self.value.setText(text)
        self.bar.setValue(0 if value is None else int(max(0, min(100, value)) * 10))
        if self.detail.text() != detail:
            self.detail.setText(detail)
        self.setToolTip(detail)

    def set_reading(self, value, detail):
        if self.value.text() != value:
            self.value.setText(value)
        if self.detail.text() != detail:
            self.detail.setText(detail)
        self.setToolTip(detail)
