"""Gera docs/assets/smartscreen.png: ilustração dos 2 cliques do aviso do SmartScreen.

Uso (na raiz do repositório):  QT_QPA_PLATFORM=offscreen python tools/make_smartscreen.py
É uma ilustração feita à mão (não é captura de tela da Microsoft).
"""
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen, QPolygonF

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets" / "smartscreen.png"
BLUE = QColor("#0063B1")
YELLOW = QColor("#FFD60A")
W, H, GAP, PAD = 500, 330, 40, 30


def font(size: int, bold: bool = False) -> QFont:
    f = QFont("DejaVu Sans")
    f.setPixelSize(size)
    f.setBold(bold)
    return f


def text(p: QPainter, x, y, w, h, s, size, bold=False, underline=False, align=Qt.AlignLeft | Qt.TextWordWrap):
    f = font(size, bold)
    f.setUnderline(underline)
    p.setFont(f)
    p.setPen(Qt.white)
    p.drawText(QRectF(x, y, w, h), int(align), s)


def button(p: QPainter, rect: QRectF, label: str, filled: bool):
    p.setBrush(Qt.white if filled else Qt.NoBrush)
    p.setPen(QPen(Qt.white, 2))
    p.drawRect(rect)
    p.setPen(QColor("#0063B1") if filled else Qt.white)
    p.setFont(font(13, True))
    p.drawText(rect, int(Qt.AlignCenter), label)


def arrow(p: QPainter, tip: QPointF, tail: QPointF, number: str):
    p.setPen(QPen(YELLOW, 5, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(tail, tip)
    d = (tip - tail)
    n = (d.x() ** 2 + d.y() ** 2) ** 0.5
    ux, uy = d.x() / n, d.y() / n
    base = QPointF(tip.x() - ux * 16, tip.y() - uy * 16)
    left = QPointF(base.x() - uy * 9, base.y() + ux * 9)
    right = QPointF(base.x() + uy * 9, base.y() - ux * 9)
    p.setBrush(YELLOW)
    p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([tip, left, right]))
    p.drawEllipse(tail, 15, 15)
    p.setPen(QColor("#141414"))
    p.setFont(font(17, True))
    p.drawText(QRectF(tail.x() - 15, tail.y() - 15, 30, 30), int(Qt.AlignCenter), number)


def panel(p: QPainter, ox: int, step2: bool):
    p.fillRect(QRectF(ox, 0, W, H), BLUE)
    x = ox + PAD
    text(p, x, 28, W - 2 * PAD, 40, "O Windows protegeu o computador", 22)
    body = (
        "O Microsoft Defender SmartScreen impediu que um aplicativo não reconhecido fosse iniciado. "
        "A execução deste aplicativo pode colocar o computador em risco."
    )
    text(p, x, 82, W - 2 * PAD, 70, body, 13)
    if not step2:
        text(p, x, 150, 200, 22, "Mais informações", 13, underline=True)
        button(p, QRectF(ox + W - PAD - 150, H - 70, 150, 40), "Não executar", True)
    else:
        text(p, x, 150, W - 2 * PAD, 22, "Aplicativo:  TeaserTube-windows-x64-setup.exe", 12)
        text(p, x, 176, W - 2 * PAD, 22, "Editor:  Editor desconhecido", 12)
        button(p, QRectF(ox + W - PAD - 340, H - 70, 180, 40), "Executar assim mesmo", False)
        button(p, QRectF(ox + W - PAD - 150, H - 70, 150, 40), "Não executar", True)


def main() -> None:
    app = QGuiApplication(sys.argv)
    total_w = 2 * W + GAP + 2 * 20
    img = QImage(total_w, H + 2 * 20 + 46, QImage.Format_ARGB32)
    img.fill(QColor("#15151a"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(20, 20)
    panel(p, 0, False)
    panel(p, W + GAP, True)
    # setas e números
    arrow(p, QPointF(PAD + 150, 163), QPointF(PAD + 235, 232), "1")
    arrow(p, QPointF(W + GAP + W - PAD - 340 + 90, H - 72), QPointF(W + GAP + W - PAD - 340 + 90, H - 128), "2")
    p.setPen(QColor("#a1a1aa"))
    p.setFont(font(13))
    p.drawText(QRectF(0, H + 8, 2 * W + GAP, 24), int(Qt.AlignCenter),
               "1) Clique em “Mais informações”        2) Clique em “Executar assim mesmo”")
    p.end()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT))
    print("imagem em", OUT)


if __name__ == "__main__":
    main()
