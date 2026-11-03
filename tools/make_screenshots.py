"""Gera as imagens do README (docs/assets/*.png) renderizando a interface fora da tela.

Uso (na raiz do repositório):  QT_QPA_PLATFORM=offscreen python tools/make_screenshots.py
Os dados são fictícios; nenhuma miniatura real é usada.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from teasertube import core, gui

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets"


def fake_thumb() -> QImage:
    img = QImage(480, 270, QImage.Format_ARGB32)
    p = QPainter(img)
    g = QLinearGradient(0, 0, 480, 270)
    g.setColorAt(0, QColor("#3b2f6b"))
    g.setColorAt(1, QColor("#e8a317"))
    p.fillRect(img.rect(), g)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(255, 255, 255, 230))
    p.setPen(QColor(0, 0, 0, 0))
    p.drawPolygon(QPolygonF([QPointF(205, 95), QPointF(205, 175), QPointF(275, 135)]))
    p.end()
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(gui.STYLE)
    w = gui.MainWindow()
    w.folder = "~/Downloads/TeaserTube"
    w.resize(1000, 680)
    w.show()
    app.processEvents(); app.processEvents()
    w.grab().save(str(OUT / "home.png"))

    info = core.MediaInfo(
        url="x", kind="playlist", title="Curso de Algoritmos", uploader="Canal de Exemplo",
        entries=[core.Entry(i, t, 420 + i * 37) for i, t in enumerate(
            ["Introdução", "Variáveis e tipos", "Condicionais", "Laços de repetição",
             "Vetores", "Funções", "Recursão", "Ordenação"], start=1)],
        single_url="y",
    )
    w._on_info((info, fake_thumb()))
    for i in (2, 6, 7):
        w.pl_list.item(i).setCheckState(gui.Qt.Unchecked)
    app.processEvents(); app.processEvents()
    w.grab().save(str(OUT / "playlist.png"))

    app.processEvents()
    w._on_progress(core.Progress("Vídeo 3 de 6 · Condicionais", 47.0, "4,2 MB/s  ·  faltam 12s"))
    w._show(w.p_progress)
    app.processEvents(); app.processEvents()
    w.grab().save(str(OUT / "progress.png"))
    print("imagens em", OUT)
    sys.stdout.flush()
    os._exit(0)  # evita um aviso inofensivo do Qt ao encerrar


if __name__ == "__main__":
    main()
