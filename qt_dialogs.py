"""Shared, non-blocking PC Monitor error dialog."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QApplication
from qt_theme import card, label, button, ORANGE, SPACE


class ErrorDialog(QDialog):
    def __init__(self, parent, title, message, details=""):
        super().__init__(parent)
        self.setWindowTitle("PC Monitor")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMinimumWidth(420)
        self.resize(490, 260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2 * SPACE, 2 * SPACE, 2 * SPACE, 2 * SPACE)
        panel, body = card()
        layout.addWidget(panel)
        header = label("!   UPOZORNĚNÍ", "muted")
        header.setStyleSheet("color: " + ORANGE + "; font-weight: 600;")
        body.addWidget(header)
        heading = label(title, "section")
        heading.setWordWrap(True)
        body.addWidget(heading)
        explanation = label(message)
        explanation.setWordWrap(True)
        body.addWidget(explanation)
        if details:
            self.details = QPlainTextEdit()
            self.details.setReadOnly(True)
            self.details.setPlainText(details)
            self.details.setMaximumHeight(160)
            self.details.hide()
            body.addWidget(self.details)
        row = QHBoxLayout()
        if details:
            self.expand = button("Technické detaily")
            self.expand.setCheckable(True)
            self.expand.toggled.connect(self.toggle_details)
            row.addWidget(self.expand)
            copy = button("Kopírovat")
            copy.clicked.connect(lambda: QApplication.clipboard().setText(details))
            row.addWidget(copy)
        row.addStretch()
        ok = button("Rozumím", True)
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        body.addLayout(row)
        ok.setFocus()

    def toggle_details(self, visible):
        self.details.setVisible(visible)
        self.expand.setText("Skrýt detaily" if visible else "Technické detaily")
        if not visible:
            self.adjustSize()
