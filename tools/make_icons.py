"""Gera icon.png, icon.ico e icon.icns a partir de teasertube/assets/icon.svg.

Uso (na raiz do repositório):  python tools/make_icons.py
Os arquivos gerados já vêm no repositório; rode isto só se mudar o logo.
"""
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parent.parent / "teasertube" / "assets"


def png_bytes(renderer: QSvgRenderer, size: int) -> bytes:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    renderer.render(p)
    p.end()
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(data)


def make_ico(pngs: dict[int, bytes]) -> bytes:
    sizes = sorted(pngs)
    out = struct.pack("<HHH", 0, 1, len(sizes))
    offset = 6 + 16 * len(sizes)
    body = b""
    for s in sizes:
        data = pngs[s]
        out += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
        body += data
    return out + body


def make_icns(pngs: dict[int, bytes]) -> bytes:
    kinds = {256: b"ic08", 512: b"ic09", 1024: b"ic10"}
    body = b"".join(kinds[s] + struct.pack(">I", len(pngs[s]) + 8) + pngs[s] for s in kinds)
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def main() -> None:
    QGuiApplication(sys.argv)
    renderer = QSvgRenderer(str(ASSETS / "icon.svg"))
    pngs = {s: png_bytes(renderer, s) for s in (16, 32, 48, 64, 128, 256, 512, 1024)}
    (ASSETS / "icon.png").write_bytes(pngs[512])
    (ASSETS / "icon.ico").write_bytes(make_ico({s: pngs[s] for s in (16, 32, 48, 64, 128, 256)}))
    (ASSETS / "icon.icns").write_bytes(make_icns(pngs))
    app_res = ASSETS.parent.parent / "TeaserTube.app" / "Contents" / "Resources"
    if app_res.exists():
        (app_res / "icon.icns").write_bytes(make_icns(pngs))
    print("ícones gerados em", ASSETS)


if __name__ == "__main__":
    main()
