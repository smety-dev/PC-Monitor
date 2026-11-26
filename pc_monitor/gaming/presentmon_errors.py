"""Human-readable capture status; do not infer permissions from exit code alone."""


def capture_error(code, stderr):
    detail = stderr.strip()
    normalized = detail.casefold()
    if "access denied" in normalized and ("trace session" in normalized or "performance log users" in normalized):
        return ("FPS měření nemá oprávnění k ETW. Na osobním PC spusť PC Monitor jako správce, "
                "nebo požádej správce o členství v Performance Log Users. "
                "Na firemním PC kontaktuj IT. Ostatní funkce zůstávají dostupné.")
    if code == 0:
        return "FPS měření skončilo. Vyber běžící proces a spusť nové měření."
    return f"PresentMon skončil (kód {code}). " + detail[-500:]
