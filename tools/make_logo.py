"""Gera teasertube/assets/logo.svg: TEASERTUB + câmera (o "E") + ondas de som.

As letras viram curvas (path), então o logo não depende de nenhuma fonte instalada.
Uso (na raiz do repositório):  python tools/make_logo.py
"""
import math
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QGuiApplication, QPainterPath
from PySide6.QtGui import QPainterPath as P

ASSETS = Path(__file__).resolve().parent.parent / "teasertube" / "assets"
YELLOW = "#FFD60A"
HEIGHT = 100.0
GAP = 12.0


def glyph(ch: str, font: QFont) -> tuple[str, float]:
    """Devolve (path SVG com altura de HEIGHT e origem em 0,0 ; largura)."""
    path = QPainterPath()
    path.addText(0, 0, font, ch)
    ref = QPainterPath()
    ref.addText(0, 0, font, "H")
    scale = HEIGHT / ref.boundingRect().height()
    rect = path.boundingRect()
    d = []
    i, n = 0, path.elementCount()

    def pt(e):
        return f"{(e.x - rect.left()) * scale:.2f} {(HEIGHT + e.y * scale):.2f}"

    while i < n:
        e = path.elementAt(i)
        if e.type == P.ElementType.MoveToElement:
            d.append("M" + pt(e))
        elif e.type == P.ElementType.LineToElement:
            d.append("L" + pt(e))
        elif e.type == P.ElementType.CurveToElement:
            c1, c2, end = e, path.elementAt(i + 1), path.elementAt(i + 2)
            d.append(f"C{pt(c1)} {pt(c2)} {pt(end)}")
            i += 2
        i += 1
    d.append("Z")
    return "".join(d), rect.width() * scale


def waves(cx: float, cy: float, radii=(20, 38, 56), sw=9, ang=38) -> str:
    a = math.radians(ang)
    out = []
    for r in radii:
        x, dy = cx + r * math.cos(a), r * math.sin(a)
        out.append(
            f'<path d="M{x:.1f} {cy - dy:.1f} A{r} {r} 0 0 1 {x:.1f} {cy + dy:.1f}" '
            f'fill="none" stroke="{YELLOW}" stroke-width="{sw}" stroke-linecap="round"/>'
        )
    return "\n    ".join(out)


def camera(ox: float) -> str:
    return (
        f'<path fill="#fff" fill-rule="evenodd" d="M{ox+14},10H{ox+70}A14 14 0 0 1 {ox+84},24V76'
        f"A14 14 0 0 1 {ox+70},90H{ox+14}A14 14 0 0 1 {ox},76V24A14 14 0 0 1 {ox+14},10Z "
        f'M{ox+30},32L{ox+30},68L{ox+60},50Z"/>\n    '
        f'<path fill="#fff" d="M{ox+91},40L{ox+120},20Q{ox+124},18 {ox+124},23V77'
        f'Q{ox+124},82 {ox+120},80L{ox+91},60Z"/>'
    )


def main() -> None:
    QGuiApplication(sys.argv)
    font = QFont("DejaVu Sans Condensed")
    font.setBold(True)
    font.setPixelSize(200)

    parts, x = [], 0.0
    for ch in "TEASERTUB":
        d, w = glyph(ch, font)
        color = "#fff" if len(parts) < 6 else YELLOW
        parts.append(f'<path fill="{color}" transform="translate({x:.1f} 0)" d="{d}"/>')
        x += w + GAP
    cam_x = x
    total = cam_x + 124 + 20 + 56 + 9
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -12 {total + 16:.0f} 124" '
        f'width="{total + 16:.0f}" height="124">\n  <g>\n    '
        + "\n    ".join(parts)
        + f"\n    {camera(cam_x)}\n    {waves(cam_x + 130, 50)}\n  </g>\n</svg>\n"
    )
    (ASSETS / "logo.svg").write_text(svg, encoding="utf-8")
    print(f"logo.svg gerado: {total + 16:.0f} x 124")


if __name__ == "__main__":
    main()
