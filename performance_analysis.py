"""Offline analysis of PC Monitor recordings in both supported CSV formats."""
import csv
import math
from concurrent.futures import CancelledError
from statistics import fmean
from performance_logger import FIELDS, CSV_HEADERS

METRICS = FIELDS[2:]
MAX_ROWS = 500_000


def number(value):
    if value is None or not value.strip():
        return None
    try:
        result = float(value.strip().replace(",", "."))
    except ValueError:
        return None
    return result if math.isfinite(result) and result >= 0 else None


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise CancelledError()


def read_recording(path, cancel=None):
    check_cancel(cancel)
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError("Duplicitní názvy sloupců.")
        mapping = dict(zip(FIELDS, CSV_HEADERS)) if set(CSV_HEADERS) <= set(headers) else dict(zip(FIELDS, FIELDS))
        if not set(mapping.values()) <= set(headers):
            raise ValueError("Soubor nemá očekávané sloupce PC Monitoru.")
        rows = []
        skipped = 0
        previous = -1
        for index, raw in enumerate(reader):
            if index % 1024 == 0:
                check_cancel(cancel)
            if index >= MAX_ROWS:
                raise ValueError("Soubor překročil limit 500 000 řádků.")
            elapsed = number(raw.get(mapping["elapsed_s"]))
            if elapsed is None or elapsed < previous:
                skipped += 1
                continue
            row = {key: number(raw.get(mapping[key])) for key in METRICS}
            row["elapsed_s"] = elapsed
            row["timestamp"] = raw.get(mapping["timestamp"], "")
            rows.append(row)
            previous = elapsed
    if not rows:
        raise ValueError("Soubor neobsahuje použitelné vzorky.")
    return rows, skipped


def summarize(rows, cancel=None):
    result = {}
    for key in METRICS:
        check_cancel(cancel)
        values = [r[key] for r in rows if r[key] is not None]
        result[key] = (min(values), fmean(values), max(values), len(values)) if values else None
    return result


def utilization_hints(rows, stats, cancel=None):
    hints = []
    for key, name, threshold in (
        ("gpu_3d_percent", "GPU 3D", 95),
        ("cpu_percent", "CPU celkem", 90),
        ("ram_percent", "RAM", 90),
    ):
        check_cancel(cancel)
        values = [r[key] for r in rows if r[key] is not None]
        if len(values) >= 5 and sum(v >= threshold for v in values) / len(values) >= .5:
            hints.append(f"{name}: nejméně polovina dostupných vzorků dosahuje {threshold} %.")
    if not hints:
        hints.append("V dostupných vzorcích nebylo zjištěno dlouhodobě vysoké celkové vytížení podle použitých prahů.")
    hints.append("Jde pouze o orientační indikaci, nikoli důkaz bottlenecku. Chybí FPS, frametimes a vytížení jednotlivých vláken v záznamu.")
    return hints
