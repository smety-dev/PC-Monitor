"""Original PC Monitor product mark shared by Qt and Windows packaging."""
import struct
from pathlib import Path
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

MARK = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect x="2" y="2" width="60" height="60" rx="14" fill="#161c25"/>
<rect x="3" y="3" width="58" height="58" rx="13" fill="none" stroke="#35465e" stroke-width="2"/>
<path d="M13 35h9l6-15 9 25 6-13h8" fill="none" stroke="#83a8ff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="50" cy="32" r="3" fill="#45dcb5"/>
</svg>"""
SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_mark(size):
    renderer = QSvgRenderer(QByteArray(MARK))
    if not renderer.isValid():
        raise ValueError("Invalid application mark")
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image


def app_icon():
    icon = QIcon()
    for size in SIZES:
        icon.addPixmap(QPixmap.fromImage(render_mark(size)))
    return icon


def write_ico(path):
    # ICO directory containing lossless PNG images, including a 256px entry.
    entries, images = [], []
    offset = 6 + 16 * len(SIZES)
    for size in SIZES:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not render_mark(size).save(buffer, "PNG"):
            raise RuntimeError("Cannot encode icon")
        data = bytes(buffer.data())
        dim = 0 if size == 256 else size
        entries.append(struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset))
        images.append(data)
        offset += len(data)
    Path(path).write_bytes(struct.pack("<HHH", 0, 1, len(entries)) + b"".join(entries + images))
