"""Settings workspace using the shared PC Monitor design system."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QDialog
from qt_theme import card, label, button, ORANGE
from version import __version__


class SettingsPage(QWidget):
    def __init__(self, prefs, reset_callback, open_gaming, open_recording):
        super().__init__()
        self.prefs = prefs
        self.reset_callback = reset_callback
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        panel, body = card()
        body.addWidget(label("Spuštění a okno", "section"))
        hint = label("Zvol, jak se má aplikace chovat při příštím spuštění.", "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.remember_page = QCheckBox("Otevřít naposledy používanou sekci")
        self.remember_geometry = QCheckBox("Zapamatovat velikost a pozici okna")
        for control in (self.remember_page, self.remember_geometry):
            body.addWidget(control)
        layout.addWidget(panel)
        self.remember_page.toggled.connect(self.save_startup)
        self.remember_geometry.toggled.connect(self.save_startup)

        panel, body = card()
        body.addWidget(label("Monitoring a herní režim", "section"))
        hint = label("Nastavení overlaye, monitoru, průhlednosti, úsporného režimu a intervalu CSV se ukládají automaticky v příslušných sekcích.", "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        row = QHBoxLayout()
        gaming = button("Nastavení Gaming")
        gaming.clicked.connect(open_gaming)
        recording = button("Nastavení záznamu")
        recording.clicked.connect(open_recording)
        row.addWidget(gaming)
        row.addWidget(recording)
        row.addStretch()
        body.addLayout(row)
        layout.addWidget(panel)

        panel, body = card()
        body.addWidget(label("Výchozí nastavení", "section"))
        hint = label("Obnoví preference aplikace. Záznamy CSV ani soubory PresentMonu se nemažou.", "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.reset_button = button("Obnovit výchozí nastavení")
        self.reset_button.setStyleSheet("color: " + ORANGE)
        self.reset_button.clicked.connect(self.confirm_reset)
        row = QHBoxLayout()
        row.addWidget(self.reset_button)
        row.addStretch()
        body.addLayout(row)
        self.status = label("Nastavení se ukládá místně pro aktuálního uživatele.", "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        layout.addWidget(panel)
        panel, body = card()
        body.addWidget(label("PC Monitor  /  v" + __version__, "section"))
        body.addWidget(label("Qt · lokální nastavení · MIT licence projektu", "muted"))
        layout.addWidget(panel)
        layout.addStretch()
        self.load()

    def load(self):
        for widget, key in ((self.remember_page, "startup/remember_page"),
                            (self.remember_geometry, "startup/remember_geometry")):
            widget.blockSignals(True)
            widget.setChecked(self.prefs.get(key))
            widget.blockSignals(False)

    def save_startup(self, *_):
        self.prefs.set("startup/remember_page", self.remember_page.isChecked())
        self.prefs.set("startup/remember_geometry", self.remember_geometry.isChecked())
        if not self.remember_geometry.isChecked():
            self.prefs.remove_geometry()
        self.prefs.sync()

    def confirm_reset(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("PC Monitor")
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        panel, body = card()
        layout.addWidget(panel)
        body.addWidget(label("Obnovit výchozí nastavení?", "section"))
        message = label("Uložené preference budou nahrazeny výchozími hodnotami. CSV a PresentMon zůstanou beze změny.", "muted")
        message.setWordWrap(True)
        body.addWidget(message)
        row = QHBoxLayout()
        cancel = button("Zrušit")
        cancel.clicked.connect(dialog.reject)
        confirm = button("Obnovit", True)
        confirm.clicked.connect(dialog.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(confirm)
        body.addLayout(row)
        cancel.setFocus()
        if dialog.exec():
            if self.reset_callback():
                self.load()
                self.status.setText("Výchozí nastavení obnoveno.")
            else:
                self.status.setText("Nejprve zastav aktivní CSV záznam.")
