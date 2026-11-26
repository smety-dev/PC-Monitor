"""Settings workspace using the shared PC Monitor design system."""
from pc_monitor.locales.i18n import tr
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QDialog, QComboBox
from pc_monitor.ui.qt_theme import card, label, button, ORANGE, SPACE
from pc_monitor.version import __version__


class SettingsPage(QWidget):
    def __init__(self, prefs, reset_callback, open_gaming, open_recording):
        super().__init__()
        self.prefs = prefs
        self.reset_callback = reset_callback
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2 * SPACE)
        panel, body = card()
        body.addWidget(label(tr("Jazyk / Language"), "section"))
        self.language = QComboBox()
        for name, code in ((tr("Systémový jazyk / System language"), "auto"), ("Čeština", "cs"), ("English", "en")):
            self.language.addItem(name, code)
        body.addWidget(self.language)
        language_hint = label(tr("Změna jazyka se projeví při příštím spuštění aplikace."), "muted")
        language_hint.setWordWrap(True)
        body.addWidget(language_hint)
        layout.addWidget(panel)
        self.language.currentIndexChanged.connect(self.save_language)
        panel, body = card()
        body.addWidget(label(tr("Spuštění a okno"), "section"))
        hint = label(tr("Zvol, jak se má aplikace chovat při příštím spuštění."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.remember_page = QCheckBox(tr("Otevřít naposledy používanou sekci"))
        self.remember_geometry = QCheckBox(tr("Zapamatovat velikost a pozici okna"))
        for control in (self.remember_page, self.remember_geometry):
            body.addWidget(control)
        layout.addWidget(panel)
        self.remember_page.toggled.connect(self.save_startup)
        self.remember_geometry.toggled.connect(self.save_startup)

        panel, body = card()
        body.addWidget(label(tr("Monitoring a herní režim"), "section"))
        hint = label(tr("Nastavení overlaye, monitoru, průhlednosti, úsporného režimu a intervalu CSV se ukládají automaticky v příslušných sekcích."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        row = QHBoxLayout()
        gaming = button(tr("Nastavení Gaming"))
        gaming.clicked.connect(open_gaming)
        recording = button(tr("Nastavení záznamu"))
        recording.clicked.connect(open_recording)
        row.addWidget(gaming)
        row.addWidget(recording)
        row.addStretch()
        body.addLayout(row)
        layout.addWidget(panel)

        panel, body = card()
        body.addWidget(label(tr("Výchozí nastavení"), "section"))
        hint = label(tr("Obnoví preference aplikace. Záznamy CSV ani soubory PresentMonu se nemažou."), "muted")
        hint.setWordWrap(True)
        body.addWidget(hint)
        self.reset_button = button(tr("Obnovit výchozí nastavení"))
        self.reset_button.setStyleSheet("color: " + ORANGE)
        self.reset_button.clicked.connect(self.confirm_reset)
        row = QHBoxLayout()
        row.addWidget(self.reset_button)
        row.addStretch()
        body.addLayout(row)
        self.status = label(tr("Nastavení se ukládá místně pro aktuálního uživatele."), "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        layout.addWidget(panel)
        panel, body = card()
        body.addWidget(label("PC Monitor  /  v" + __version__, "section"))
        body.addWidget(label(tr("Qt · lokální nastavení · MIT licence projektu"), "muted"))
        layout.addWidget(panel)
        layout.addStretch()
        self.load()

    def save_language(self, *_):
        self.prefs.set("ui/language", self.language.currentData())
        self.prefs.sync()
        self.status.setText(tr("Jazyk uložen. Restartuj aplikaci, až budeš mít hotová měření."))

    def load(self):
        self.language.blockSignals(True)
        self.language.setCurrentIndex(self.language.findData(self.prefs.get("ui/language")))
        self.language.blockSignals(False)
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
        body.addWidget(label(tr("Obnovit výchozí nastavení?"), "section"))
        message = label(tr("Uložené preference budou nahrazeny výchozími hodnotami. CSV a PresentMon zůstanou beze změny."), "muted")
        message.setWordWrap(True)
        body.addWidget(message)
        row = QHBoxLayout()
        cancel = button(tr("Zrušit"))
        cancel.clicked.connect(dialog.reject)
        confirm = button(tr("Obnovit nastavení"), True)
        confirm.clicked.connect(dialog.accept)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(confirm)
        body.addLayout(row)
        cancel.setFocus()
        if dialog.exec():
            if self.reset_callback():
                self.load()
                self.status.setText(tr("Výchozí nastavení obnoveno."))
            else:
                self.status.setText(tr("Nejprve zastav aktivní CSV záznam."))
