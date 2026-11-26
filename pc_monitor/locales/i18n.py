"""Application language is resolved once per window startup; data formats stay stable."""
import re
from pc_monitor.locales.locale_en import EN

LANGUAGES = ("auto", "cs", "en")
_language = "cs"


def resolve_language(choice, system_locale=None):
    if choice in ("cs", "en"):
        return choice
    if system_locale is None:
        from PySide6.QtCore import QLocale
        system_locale = QLocale.system().name()
    return "cs" if str(system_locale).lower().replace("-", "_").split("_")[0] == "cs" else "en"


def set_language(choice, system_locale=None):
    global _language
    _language = resolve_language(choice, system_locale)
    return _language


def language():
    return _language


def decimal(text):
    return text.replace(".", ",") if _language == "cs" else text


# Dynamic display strings. Only explicitly recognized UI patterns are translated.
_PATTERNS = (
    (r"(.+) fyzických jader / (.+) vláken · frekvence hlášená OS", r"\1 physical cores / \2 threads · OS-reported frequency"),
    (r"(.+) jader / (.+) vláken", r"\1 cores / \2 threads"),
    (r"(.+) GiB volných z (.+) GiB", r"\1 GiB free of \2 GiB"),
    (r"(.+) GiB volné", r"\1 GiB free"),
    (r"(.+) s zpět", r"\1 s ago"),
    (r"(\d+) / (\d+) procesů", r"\1 / \2 processes"),
    (r"(\d+) z (\d+) procesů", r"\1 of \2 processes"),
    (r"(.+) vzorků  ·  (.+) s  ·  vynecháno (\d+)", r"\1 samples  ·  \2 s  ·  skipped \3"),
    (r"(.+) vzorků  ·  (.+) s", r"\1 samples  ·  \2 s"),
    (r"Měřím • (\d+) vzorků / max\. 10 s • swap chain (.+)", r"Capturing • \1 samples / max. 10 s • swap chain \2"),
    (r"● Probíhá měření · (.+) / (.+) s · (\d+) snímků", r"● Capturing · \1 / \2 s · \3 frames"),
    (r"Průměr FPS: (.+)", r"Average FPS: \1"),
    (r"PresentMon skončil \(kód (.+)\)\. (.*)", r"PresentMon exited (code \1). \2"),
    (r"PresentMon neočekávaně skončil \(kód (.+)\)\.", r"PresentMon exited unexpectedly (code \1)."),
    (r"(.+): nejméně polovina dostupných vzorků dosahuje (\d+) %\.", r"\1: at least half of available samples reach \2 %."),
)


def tr(text):
    if _language != "en" or not isinstance(text, str):
        return text
    if text in EN:
        return EN[text]
    for pattern, replacement in _PATTERNS:
        if re.fullmatch(pattern, text, re.DOTALL):
            return re.sub(pattern, replacement, text, count=1, flags=re.DOTALL).replace("CPU celkem:", "Total CPU:")
    return text
