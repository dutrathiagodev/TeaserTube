"""Interface gráfica (PySide6): cola o link, escolhe as opções e baixa."""
from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSettings, QSize, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QDesktopServices,
    QBrush,
    QColor,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import __version__, core, updater

APP_NAME = "TeaserTube"
ASSETS = Path(__file__).parent / "assets"

BG = QColor("#0b0b0d")
GLOW = QColor("#26262b")
LINE = QColor(170, 170, 180, 190)
YELLOW = "#FFD60A"

QUALITIES = ["Melhor qualidade", "1080p", "720p", "480p", "360p"]
CHECK_ICON = (ASSETS / "check.svg").as_posix()  # ✓ amarelo das caixinhas marcadas

STYLE = f"""
* {{ font-family: "Inter", "Segoe UI", "Ubuntu", "Helvetica Neue", Arial, sans-serif; }}
QLabel {{ color: #f4f4f5; background: transparent; }}
#card {{ background: #15151a; border: 1px solid #2c2c35; border-radius: 22px; }}
#subtitle, #muted {{ color: #9a9aa6; }}
#title {{ font-size: 24px; font-weight: 700; color: #ffffff; }}
#bigTitle {{ font-size: 20px; font-weight: 700; }}
#error {{ color: #ff6b6b; }}
#failBox {{ background: #1d1719; border: 1px solid #4a2f35; border-radius: 12px; }}
#updateBanner {{ background: rgba(255, 214, 10, 30); border: 1px solid rgba(255, 214, 10, 110); border-radius: 12px; }}
#updateText {{ color: #ffe14d; font-weight: 600; }}
#updBtn {{ background: {YELLOW}; color: #141414; padding: 7px 16px; font-size: 13px; border-radius: 10px; }}
#updBtn:hover {{ background: #ffe14d; }}
#updBtn:disabled {{ background: #5c5220; color: #2b2b2b; }}
#updLater {{ background: transparent; color: #b4b4be; padding: 7px 12px; font-size: 13px; }}
#updLater:hover {{ color: #ffffff; background: transparent; }}
#failTitle {{ color: #ff9a9a; font-weight: 600; }}
#inputRow {{ background: #1f1f26; border: 1px solid #2c2c35; border-radius: 16px; }}
#inputRow:focus-within {{ border: 1px solid {YELLOW}; }}
QLineEdit {{ background: transparent; border: none; color: #f4f4f5; font-size: 14px;
            padding: 10px 8px; selection-background-color: {YELLOW}; selection-color: #111; }}
QPushButton {{ border: none; border-radius: 12px; padding: 11px 22px; font-size: 14px;
              font-weight: 600; color: #f4f4f5; background: #26262e; }}
QPushButton:hover {{ background: #30303a; }}
QPushButton:disabled {{ color: #6b6b75; background: #1f1f26; }}
#primary {{ background: {YELLOW}; color: #141414; }}
#primary:hover {{ background: #ffe14d; }}
#primary:disabled {{ background: #5c5220; color: #2b2b2b; }}
#ghost {{ background: transparent; color: #b4b4be; }}
#ghost:hover {{ background: #22222a; color: #fff; }}
#link {{ background: transparent; color: {YELLOW}; padding: 4px 0; text-align: left; font-weight: 500; }}
#link:hover {{ color: #ffe14d; }}
#seg {{ background: #1f1f26; color: #b4b4be; border-radius: 12px; padding: 10px 18px; }}
#seg:checked {{ background: {YELLOW}; color: #141414; }}
#seg:!checked:hover {{ background: #2a2a33; }}
QComboBox {{ background: #1f1f26; border: 1px solid #2c2c35; border-radius: 12px; padding: 9px 14px;
            padding-right: 34px; color: #f4f4f5; font-size: 14px; min-height: 22px; }}
QComboBox:hover {{ border-color: #44444f; }}
QComboBox::drop-down {{ border: none; width: 32px; }}
QComboBox QFrame {{ background: #1f1f26; border: none; }}
QComboBox QAbstractItemView {{ background: #1f1f26; color: #f4f4f5; border: 1px solid #2c2c35;
            selection-background-color: {YELLOW}; selection-color: #111; outline: none; padding: 4px; }}
QProgressBar {{ background: #26262e; border: none; border-radius: 6px; height: 12px; }}
QProgressBar::chunk {{ background: {YELLOW}; border-radius: 6px; }}
QListWidget {{ background: #1a1a20; border: 1px solid #2c2c35; border-radius: 12px; color: #e4e4e7;
              padding: 4px; outline: none; font-size: 13px; }}
QListWidget::item {{ padding: 5px 4px; border-radius: 6px; }}
QListWidget::item:hover {{ background: #24242c; }}
QListWidget::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1.5px solid #55555f;
              background: #1f1f26; }}
QListWidget::indicator:hover {{ border-color: #8a8a95; }}
QListWidget::indicator:checked {{ background: rgba(255, 214, 10, 48); border: 1.5px solid {YELLOW};
              image: url({CHECK_ICON}); }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #3a3a44; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def app_root() -> Path:
    """Pasta do software (onde fica o app); os downloads vão para <pasta>/downloads."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def default_folder() -> str:
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        return str(Path.home() / "Downloads" / "TeaserTube")  # não dá para gravar dentro do .app
    return str(app_root() / "downloads")


def open_folder(path: str) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def free_bytes(path: str) -> int:
    """Espaço livre no disco da pasta (sobe até a pasta existente mais próxima)."""
    p = Path(path).expanduser()
    while not p.exists() and p != p.parent:
        p = p.parent
    try:
        return shutil.disk_usage(p).free
    except OSError:
        return 0


def fmt_duration(seconds) -> str:
    if not seconds:
        return ""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def svg_icon(name: str) -> QIcon:
    icon = QIcon()
    renderer = QSvgRenderer(str(ASSETS / name))
    for size in (16, 24, 32, 48, 64, 128, 256):
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        renderer.render(p)
        p.end()
        icon.addPixmap(pm)
    return icon


def rounded(pixmap: QPixmap, radius: int) -> QPixmap:
    out = QPixmap(pixmap.size())
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(out.rect()), radius, radius)
    p.setClipPath(path)
    p.drawPixmap(0, 0, pixmap)
    p.end()
    return out


# --------------------------------------------------------------------------- #
# Widgets
# --------------------------------------------------------------------------- #
class GridBackground(QWidget):
    """Fundo escuro com grade que some nas bordas."""

    CELL = 52

    def paintEvent(self, _event) -> None:
        w, h = self.width(), self.height()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.fillRect(self.rect(), BG)
        cx, cy = w / 2, h / 2

        def ellipse_gradient(stops) -> QRadialGradient:
            g = QRadialGradient(QPointF(0, 0), 1.0)
            for pos, color in stops:
                g.setColorAt(pos, color)
            return g

        p.save()
        p.translate(cx, cy)
        p.scale(w * 0.62, h * 0.62)
        p.fillRect(QRectF(-1, -1, 2, 2), QBrush(ellipse_gradient([(0, GLOW), (1, BG)])))
        p.restore()

        p.setPen(QPen(LINE, 1))
        x = cx - (cx // self.CELL + 1) * self.CELL
        while x <= w:
            p.drawLine(int(x), 0, int(x), h)
            x += self.CELL
        y = cy - (cy // self.CELL + 1) * self.CELL
        while y <= h:
            p.drawLine(0, int(y), w, int(y))
            y += self.CELL

        clear = QColor(BG)
        clear.setAlpha(0)
        p.save()
        p.translate(cx, cy)
        p.scale(w * 0.62, h * 0.62)
        p.fillRect(
            QRectF(-1, -1, 2, 2),
            QBrush(ellipse_gradient([(0, clear), (0.5, clear), (0.95, BG), (1, BG)])),
        )
        p.restore()


class Combo(QComboBox):
    """ComboBox com a seta desenhada (o QSS remove a padrão)."""

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#b4b4be"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        x, y = self.width() - 22, self.height() / 2
        p.drawLine(QPointF(x - 4, y - 2), QPointF(x, y + 2))
        p.drawLine(QPointF(x, y + 2), QPointF(x + 4, y - 2))


class StatusBadge(QWidget):
    """Círculo com ✓ (ok), ! (aviso) ou ✕ (erro), desenhado à mão."""

    COLORS = {"ok": "#FFD60A", "warn": "#FFB020", "error": "#FF6B6B"}

    def __init__(self) -> None:
        super().__init__()
        self.state = "ok"
        self.setFixedSize(76, 76)

    def set_state(self, state: str) -> None:
        self.state = state
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        color = QColor(self.COLORS[self.state])
        halo = QColor(color)
        halo.setAlpha(40)
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QRectF(0, 0, 76, 76))
        p.setBrush(color)
        p.drawEllipse(QRectF(10, 10, 56, 56))
        p.setPen(QPen(QColor("#141414"), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if self.state == "ok":
            p.drawPolyline([QPointF(26, 39), QPointF(34, 47), QPointF(51, 29)])
        elif self.state == "warn":
            p.drawLine(QPointF(38, 25), QPointF(38, 42))
            p.drawPoint(QPointF(38, 51))
        else:
            p.drawLine(QPointF(28, 28), QPointF(48, 48))
            p.drawLine(QPointF(48, 28), QPointF(28, 48))


class Task(QThread):
    """Executa uma função fora da thread da interface."""

    finished_ok = Signal(object)
    failed = Signal(str)
    progress = Signal(object)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self) -> None:
        try:
            self.finished_ok.emit(self.fn(self))
        except core.Cancelled:
            self.failed.emit("")
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(core.clean_error(exc))


def label(text: str = "", name: str = "", wrap: bool = False, align=None) -> QLabel:
    lb = QLabel(text)
    lb.setTextFormat(Qt.PlainText)  # títulos vêm da internet: nunca interpretar como HTML
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    if align:
        lb.setAlignment(align)
    return lb


# --------------------------------------------------------------------------- #
# Janela principal
# --------------------------------------------------------------------------- #
class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — baixador de vídeos e áudios")
        self.setWindowIcon(svg_icon("icon.svg"))
        self.resize(1000, 680)
        self.setMinimumSize(780, 640)

        self.settings = QSettings("teasertube", "teasertube")
        self.folder = self.settings.value("folder", default_folder())
        self.info: core.MediaInfo | None = None
        self.task: Task | None = None
        self.cancel = threading.Event()
        self.result: core.Result | None = None

        self.bg = GridBackground(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.bg)
        center = QVBoxLayout(self.bg)
        center.setContentsMargins(24, 24, 24, 24)
        center.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)
        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedWidth(680)
        shadow = QGraphicsDropShadowEffect(blurRadius=60, xOffset=0, yOffset=18)
        shadow.setColor(QColor(0, 0, 0, 190))
        self.card.setGraphicsEffect(shadow)
        row.addWidget(self.card)
        row.addStretch(1)
        center.addLayout(row)
        center.addStretch(1)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(36, 32, 36, 32)
        card_layout.setSpacing(16)
        self.update_info: updater.UpdateInfo | None = None
        self.update_cancel = threading.Event()
        self._bg_tasks: list[Task] = []
        self.update_banner = QFrame()
        self.update_banner.setObjectName("updateBanner")
        bl = QHBoxLayout(self.update_banner)
        bl.setContentsMargins(14, 10, 10, 10)
        self.update_text = label("", "updateText", wrap=True)
        self.update_btn = QPushButton("Atualizar")
        self.update_btn.setObjectName("updBtn")
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self.on_update)
        self.update_later = QPushButton("Depois")
        self.update_later.setObjectName("updLater")
        self.update_later.setCursor(Qt.PointingHandCursor)
        self.update_later.clicked.connect(self._hide_update_banner)
        bl.addWidget(self.update_text, 1)
        bl.addWidget(self.update_btn)
        bl.addWidget(self.update_later)
        self.update_banner.hide()
        card_layout.addWidget(self.update_banner)
        self.stack = QStackedWidget()
        card_layout.addWidget(self.stack)

        self.p_home = self._build_home()
        self.p_loading = self._build_loading()
        self.p_options = self._build_options()
        self.p_progress = self._build_progress()
        self.p_result = self._build_result()
        for page in (self.p_home, self.p_loading, self.p_options, self.p_progress, self.p_result):
            self.stack.addWidget(page)
        self.stack.currentChanged.connect(self._fit_stack)
        self._show(self.p_home)

    # ----- navegação --------------------------------------------------------
    def _fit_stack(self, _index: int = 0) -> None:
        """A altura do cartão acompanha só a página visível (o QStackedWidget usa a maior)."""
        page = self.stack.currentWidget()
        lay = page.layout()
        width = self.card.width() - 72
        height = lay.totalHeightForWidth(width) if lay.hasHeightForWidth() else 0
        self.stack.setFixedHeight(max(height, lay.totalSizeHint().height()))
        card_layout = self.card.layout()
        card_layout.invalidate()
        card_layout.activate()
        self.card.setFixedHeight(card_layout.sizeHint().height())

    def _show(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(page)
        self._fit_stack()
        QTimer.singleShot(0, self._fit_stack)  # reajusta depois que o Qt calcula os tamanhos

    # ----- páginas ----------------------------------------------------------
    def _build_home(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(14)
        lay.setContentsMargins(0, 0, 0, 0)

        logo = QSvgWidget(str(ASSETS / "logo.svg"))
        logo.setFixedSize(QSize(560, 68))
        lay.addWidget(logo, alignment=Qt.AlignHCenter)
        lay.addSpacing(6)
        lay.addWidget(
            label(
                "Baixador de vídeos e áudios. Cole o link de um vídeo ou playlist do YouTube e escolha o formato.",
                "subtitle",
                wrap=True,
                align=Qt.AlignHCenter,
            )
        )
        lay.addSpacing(6)

        box = QFrame()
        box.setObjectName("inputRow")
        h = QHBoxLayout(box)
        h.setContentsMargins(14, 6, 6, 6)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Cole aqui o URL do vídeo ou da playlist")
        self.url_edit.returnPressed.connect(self.on_search)
        self.url_edit.setClearButtonEnabled(True)
        h.addWidget(self.url_edit, 1)
        self.search_btn = QPushButton("Buscar")
        self.search_btn.setObjectName("primary")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self.on_search)
        h.addWidget(self.search_btn)
        lay.addWidget(box)

        self.home_error = label("", "error", wrap=True, align=Qt.AlignHCenter)
        self.home_error.hide()
        lay.addWidget(self.home_error)
        lay.addWidget(
            label(
                "Use apenas para conteúdo que você tem o direito de baixar.",
                "muted",
                align=Qt.AlignHCenter,
            )
        )
        self.version_btn = QPushButton(f"v{__version__}  ·  Verificar atualizações")
        self.version_btn.setObjectName("link")
        self.version_btn.setCursor(Qt.PointingHandCursor)
        self.version_btn.clicked.connect(lambda: self._check_updates(manual=True))
        lay.addWidget(self.version_btn, alignment=Qt.AlignHCenter)
        return page

    def _build_loading(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(18)
        lay.addSpacing(30)
        lay.addWidget(label("Buscando informações…", "bigTitle", align=Qt.AlignHCenter))
        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setTextVisible(False)
        lay.addWidget(bar)
        lay.addSpacing(30)
        return page

    def _build_options(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(18)
        self.thumb = QLabel()
        self.thumb.setFixedSize(224, 126)
        self.thumb.setStyleSheet("background:#1f1f26; border-radius:12px;")
        top.addWidget(self.thumb, alignment=Qt.AlignTop)
        meta = QVBoxLayout()
        meta.setSpacing(4)
        self.opt_title = label("", "bigTitle", wrap=True)
        self.opt_meta = label("", "muted", wrap=True)
        meta.addWidget(self.opt_title)
        meta.addWidget(self.opt_meta)
        self.single_btn = QPushButton("Baixar só este vídeo (sem a playlist)")
        self.single_btn.setObjectName("link")
        self.single_btn.setCursor(Qt.PointingHandCursor)
        self.single_btn.clicked.connect(self.on_single)
        meta.addWidget(self.single_btn, alignment=Qt.AlignLeft)
        meta.addStretch(1)
        top.addLayout(meta, 1)
        lay.addLayout(top)

        self.live_note = label("", "error", wrap=True)
        self.live_note.hide()
        lay.addWidget(self.live_note)

        # Playlist: lista de vídeos com caixas de seleção
        self.playlist_box = QWidget()
        pl = QVBoxLayout(self.playlist_box)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(6)
        head = QHBoxLayout()
        self.pl_count = label("", "muted")
        head.addWidget(self.pl_count, 1)
        all_btn = QPushButton("Todos")
        all_btn.setObjectName("link")
        none_btn = QPushButton("Nenhum")
        none_btn.setObjectName("link")
        for b, state in ((all_btn, Qt.Checked), (none_btn, Qt.Unchecked)):
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, s=state: self._check_all(s))
            head.addWidget(b)
        pl.addLayout(head)
        self.pl_list = QListWidget()
        self.pl_list.setFixedHeight(150)
        self.pl_list.itemChanged.connect(self._update_count)
        pl.addWidget(self.pl_list)
        lay.addWidget(self.playlist_box)

        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)
        self.btn_video = QPushButton("Vídeo · MP4")
        self.btn_audio = QPushButton("Áudio · MP3")
        self.fmt_group = QButtonGroup(self)
        for i, b in enumerate((self.btn_video, self.btn_audio)):
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            self.fmt_group.addButton(b, i)
            fmt_row.addWidget(b)
        self.btn_video.setChecked(True)
        self.fmt_group.idToggled.connect(self._format_changed)
        fmt_row.addSpacing(8)
        self.quality = Combo()
        self.quality.setMinimumWidth(260)
        self.quality.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.quality.currentIndexChanged.connect(self._update_size_hint)
        fmt_row.addWidget(self.quality)
        fmt_row.addStretch(1)
        lay.addLayout(fmt_row)

        self.size_hint = label("", "muted", wrap=True)
        lay.addWidget(self.size_hint)

        folder_row = QHBoxLayout()
        folder_row.addWidget(label("Salvar em", "muted"))
        self.folder_label = label("", wrap=False)
        self.folder_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        folder_row.addWidget(self.folder_label, 1)
        change = QPushButton("Alterar")
        change.setObjectName("ghost")
        change.setCursor(Qt.PointingHandCursor)
        change.clicked.connect(self.on_change_folder)
        folder_row.addWidget(change)
        lay.addLayout(folder_row)

        btns = QHBoxLayout()
        back = QPushButton("Voltar")
        back.setObjectName("ghost")
        back.setCursor(Qt.PointingHandCursor)
        back.clicked.connect(self.on_back)
        self.download_btn = QPushButton("Baixar")
        self.download_btn.setObjectName("primary")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setMinimumWidth(160)
        self.download_btn.clicked.connect(self.on_download)
        btns.addWidget(back)
        btns.addStretch(1)
        btns.addWidget(self.download_btn)
        lay.addLayout(btns)
        return page

    def _build_progress(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(14)
        lay.addSpacing(10)
        self.prog_title = label("Baixando…", "bigTitle", wrap=True, align=Qt.AlignHCenter)
        lay.addWidget(self.prog_title)
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 1000)
        self.prog_bar.setTextVisible(False)
        lay.addWidget(self.prog_bar)
        self.prog_detail = label("", "muted", align=Qt.AlignHCenter)
        lay.addWidget(self.prog_detail)
        lay.addSpacing(8)
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("ghost")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.on_cancel)
        lay.addWidget(cancel, alignment=Qt.AlignHCenter)
        return page

    def _build_result(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)
        self.res_badge = StatusBadge()
        lay.addWidget(self.res_badge, alignment=Qt.AlignHCenter)
        self.res_title = label("", "bigTitle", align=Qt.AlignHCenter)
        lay.addWidget(self.res_title)
        self.res_msg = label("", "muted", wrap=True, align=Qt.AlignHCenter)
        lay.addWidget(self.res_msg)

        self.fail_box = QFrame()
        self.fail_box.setObjectName("failBox")
        fl = QVBoxLayout(self.fail_box)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(6)
        self.fail_title = label("", "failTitle")
        self.fail_list = label("", wrap=True)
        self.fail_list.setTextFormat(Qt.RichText)
        fl.addWidget(self.fail_title)
        fl.addWidget(self.fail_list)
        lay.addWidget(self.fail_box)

        lay.addSpacing(6)
        row = QHBoxLayout()
        row.addStretch(1)
        self.res_open = QPushButton("Abrir pasta")
        self.res_open.setCursor(Qt.PointingHandCursor)
        self.res_open.clicked.connect(lambda: self.result and open_folder(self.result.folder))
        self.res_again = QPushButton("Baixar outro")
        self.res_again.setObjectName("primary")
        self.res_again.setCursor(Qt.PointingHandCursor)
        self.res_again.clicked.connect(self.on_back_home)
        row.addWidget(self.res_open)
        row.addWidget(self.res_again)
        row.addStretch(1)
        lay.addLayout(row)
        return page

    # ----- ações ------------------------------------------------------------
    def on_search(self, url: str | None = None, single: bool = False) -> None:
        url = core.normalize_url(url if isinstance(url, str) else self.url_edit.text())
        if not url or " " in url:
            self._home_error("Cole um link válido.")
            return
        self.home_error.hide()
        self._show(self.p_loading)

        def work(_task: Task):
            info = core.fetch_info(url, single=single)
            image = QImage()
            if info.thumbnail and info.thumbnail.lower().startswith("https://"):
                try:
                    req = urllib.request.Request(info.thumbnail, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        image.loadFromData(r.read(5_000_000))  # no máximo 5 MB
                except Exception:  # noqa: BLE001
                    pass
            return info, image

        self.task = Task(work, self)
        self.task.finished_ok.connect(self._on_info)
        self.task.failed.connect(self._on_info_error)
        self.task.start()

    def on_single(self) -> None:
        if self.info and self.info.single_url:
            self.on_search(self.info.single_url, single=True)

    def _home_error(self, msg: str) -> None:
        self.home_error.setText(msg)
        self.home_error.show()
        self._show(self.p_home)
        self._fit_stack()

    def _on_info_error(self, msg: str) -> None:
        self._home_error(msg or "Não foi possível ler esse link.")

    def _on_info(self, payload) -> None:
        info, image = payload
        self.info = info
        is_pl = info.kind == "playlist"

        self.opt_title.setText(info.title)
        if is_pl:
            self.opt_meta.setText(f"{info.uploader}\nPlaylist · {len(info.entries)} vídeos".strip())
        else:
            self.opt_meta.setText(
                "  ·  ".join(x for x in (info.uploader, fmt_duration(info.duration)) if x)
            )
        if image.isNull():
            self.thumb.clear()
        else:
            pm = QPixmap.fromImage(image).scaled(
                self.thumb.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (pm.width() - self.thumb.width()) // 2
            y = (pm.height() - self.thumb.height()) // 2
            self.thumb.setPixmap(rounded(pm.copy(x, y, self.thumb.width(), self.thumb.height()), 12))

        self.single_btn.setVisible(is_pl and bool(info.single_url))
        self.playlist_box.setVisible(is_pl)
        if is_pl:
            self.pl_list.blockSignals(True)
            self.pl_list.clear()
            for e in info.entries:
                dur = f"  ({fmt_duration(e.duration)})" if e.duration else ""
                item = QListWidgetItem(f"{e.index:02d}  {e.title}{dur}")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, e.index)
                self.pl_list.addItem(item)
            self.pl_list.blockSignals(False)
            self._update_count()

        self._fill_qualities()
        self.folder_label.setText(self._elide(self.folder))
        self.live_note.setVisible(info.is_ongoing)
        if info.is_ongoing:
            self.live_note.setText(
                "Esta transmissão ainda não terminou."
                if info.live_status == "is_live"
                else "Esta transmissão ainda não começou."
            )
            self.live_note.setText(self.live_note.text() + " Quando acabar, volte aqui e baixe a gravação.")
        if not is_pl:
            self.download_btn.setEnabled(not info.is_ongoing)
        self._show(self.p_options)

    def _fill_qualities(self) -> None:
        self.quality.blockSignals(True)
        self.quality.clear()
        info = self.info
        if self.btn_audio.isChecked():
            size = core.fmt_size(core.estimate_bytes(info, "audio", None)) if info else ""
            self.quality.addItem("MP3 · 192 kbps" + (f" · ~{size}" if size else ""))
            self.quality.setEnabled(False)
        else:
            self.quality.setEnabled(True)

            def add(text: str, height) -> None:
                size = core.fmt_size(core.estimate_bytes(info, "video", height)) if info else ""
                self.quality.addItem(text + (f" · ~{size}" if size else ""), height)

            best = max((h for h in info.heights if h >= 144), default=None) if info and info.kind == "video" else None
            add(f"Melhor ({best}p)" if best else "Melhor qualidade", None)
            if info and info.kind == "video" and info.heights:
                for h in info.heights:
                    if h >= 144:
                        add(f"{h}p", h)
            else:
                for h in (1080, 720, 480, 360):
                    add(f"{h}p", h)
        self.quality.blockSignals(False)
        self._update_size_hint()

    def _update_size_hint(self, *_args) -> None:
        """Mostra o tamanho estimado e avisa se o disco não aguenta."""
        info = self.info
        if not info:
            self.size_hint.hide()
            return
        self.size_hint.show()
        if info.kind != "video":  # playlist: o tamanho de cada vídeo ainda não é conhecido
            self.size_hint.setText(f"Espaço livre na pasta: {core.fmt_size(free_bytes(self.folder))}")
            self.size_hint.setStyleSheet("")
            return
        mode = "audio" if self.btn_audio.isChecked() else "video"
        height = self.quality.currentData() if mode == "video" else None
        estimate = core.estimate_bytes(info, mode, height)
        free = free_bytes(self.folder)
        if not estimate:
            self.size_hint.setText(f"Espaço livre na pasta: {core.fmt_size(free)}")
            self.size_hint.setStyleSheet("")
            return
        needed = core.disk_needed(estimate)
        if free and free < needed:
            self.size_hint.setText(
                f"Espaço insuficiente: precisa de ~{core.fmt_size(needed)} livres "
                f"(durante a junção de vídeo e áudio o arquivo fica duplicado) e a pasta tem {core.fmt_size(free)}."
            )
            self.size_hint.setStyleSheet("color:#ff8a8a;")
        else:
            self.size_hint.setText(
                f"Tamanho estimado: ~{core.fmt_size(estimate)}  ·  espaço livre: {core.fmt_size(free)}"
            )
            self.size_hint.setStyleSheet("")

    def _format_changed(self, _id: int, checked: bool) -> None:
        if checked:
            self._fill_qualities()

    def _check_all(self, state) -> None:
        self.pl_list.blockSignals(True)
        for i in range(self.pl_list.count()):
            self.pl_list.item(i).setCheckState(state)
        self.pl_list.blockSignals(False)
        self._update_count()

    def _selected(self) -> list[int]:
        return [
            self.pl_list.item(i).data(Qt.UserRole)
            for i in range(self.pl_list.count())
            if self.pl_list.item(i).checkState() == Qt.Checked
        ]

    def _update_count(self, *_args) -> None:
        n = len(self._selected())
        self.pl_count.setText(f"{n} de {self.pl_list.count()} vídeos selecionados")
        self.download_btn.setEnabled(n > 0)

    def _elide(self, path: str) -> str:
        return path if len(path) <= 48 else "…" + path[-47:]

    def on_change_folder(self) -> None:
        start = self.folder if os.path.isdir(self.folder) else str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Escolha a pasta", start)
        if chosen:
            self.folder = chosen
            self.settings.setValue("folder", chosen)
            self.folder_label.setText(self._elide(chosen))
            self._update_size_hint()

    def on_back(self) -> None:
        self._show(self.p_home)
        self.url_edit.setFocus()

    def on_back_home(self) -> None:
        self.url_edit.clear()
        self.on_back()

    def on_download(self) -> None:
        if not self.info:
            return
        info = self.info
        mode = "audio" if self.btn_audio.isChecked() else "video"
        height = self.quality.currentData() if mode == "video" else None
        selected = self._selected() if info.kind == "playlist" else None
        estimate = core.estimate_bytes(info, mode, height)
        if estimate and free_bytes(self.folder) < core.disk_needed(estimate):
            self._on_fail(
                f"Espaço insuficiente no disco: o download precisa de ~{core.fmt_size(core.disk_needed(estimate))} "
                f"livres e a pasta tem {core.fmt_size(free_bytes(self.folder))}. "
                "Escolha outra pasta (botão Alterar) ou uma qualidade menor."
            )
            return
        os.makedirs(self.folder, exist_ok=True)
        self.cancel = threading.Event()
        cancel = self.cancel
        folder = self.folder

        self.prog_title.setText("Preparando…")
        self.prog_detail.setText("")
        self.prog_bar.setRange(0, 0)
        self._show(self.p_progress)

        def work(task: Task):
            return core.download(info, mode, height, folder, selected, task.progress.emit, cancel)

        self.task = Task(work, self)
        self.task.progress.connect(self._on_progress)
        self.task.finished_ok.connect(self._on_done)
        self.task.failed.connect(self._on_fail)
        self.task.start()

    def _on_progress(self, pr: core.Progress) -> None:
        self.prog_title.setText(pr.stage)
        self.prog_detail.setText(pr.detail)
        if pr.percent is None:
            self.prog_bar.setRange(0, 0)
        else:
            self.prog_bar.setRange(0, 1000)
            self.prog_bar.setValue(int(pr.percent * 10))

    def on_cancel(self) -> None:
        self.cancel.set()
        self.prog_title.setText("Cancelando…")

    def _on_done(self, result: core.Result) -> None:
        self.result = result
        n = len(result.files)
        ok = not result.failures
        self.res_badge.set_state("ok" if ok else "warn")
        self.res_title.setText("Download concluído!" if ok else "Concluído, mas com avisos")
        what = os.path.basename(result.files[0]) if n == 1 else f"{n} arquivos salvos"
        self.res_msg.setText(f"{what}\n{result.folder}")

        self.fail_box.setVisible(not ok)
        if not ok:
            k = len(result.failures)
            self.fail_title.setText(
                "1 vídeo não foi baixado" if k == 1 else f"{k} vídeos não foram baixados"
            )
            lines = [
                f"• <b>{html.escape(f.title)}</b><br/>"
                f"<span style='color:#b4b4be'>&nbsp;&nbsp;{html.escape(f.reason)}</span>"
                for f in result.failures[:5]
            ]
            if k > 5:
                lines.append(f"<span style='color:#b4b4be'>… e mais {k - 5}.</span>")
            self.fail_list.setText("<br/>".join(lines))
        self.res_open.show()
        self.res_again.setText("Baixar outro")
        self._show(self.p_result)

    def _on_fail(self, msg: str) -> None:
        if not msg:  # cancelado
            self._show(self.p_options)
            return
        self.result = None
        self.res_badge.set_state("error")
        self.res_title.setText("Algo deu errado")
        self.res_msg.setText(msg)
        self.fail_box.hide()
        self.res_open.hide()
        self.res_again.setText("Voltar")
        self._show(self.p_result)

    # ----- atualizações -----------------------------------------------------
    def _keep(self, task: Task) -> Task:
        """Guarda a referência da tarefa até ela terminar (senão o Qt a destrói no meio)."""
        self._bg_tasks.append(task)
        task.finished.connect(lambda t=task: self._bg_tasks.remove(t) if t in self._bg_tasks else None)
        return task

    def _reset_version_btn(self) -> None:
        self.version_btn.setText(f"v{__version__}  ·  Verificar atualizações")

    def _check_updates(self, manual: bool = False) -> None:
        if not manual and os.environ.get("TEASERTUBE_NO_UPDATE_CHECK"):
            return
        if manual:
            self.version_btn.setText("Verificando…")
        task = self._keep(Task(lambda _t: updater.check(), self))
        task.finished_ok.connect(lambda upd: self._on_update_checked(upd, manual))
        task.failed.connect(lambda _msg: self._on_update_check_failed(manual))
        task.start()

    def _on_update_checked(self, upd, manual: bool) -> None:
        if upd:
            self._show_update(upd)
            self._reset_version_btn()
        elif manual:
            self.version_btn.setText("✓ Você já está na versão mais recente")
            QTimer.singleShot(5000, self._reset_version_btn)

    def _on_update_check_failed(self, manual: bool) -> None:
        if manual:  # na verificação automática falhar em silêncio é o certo (sem internet, por exemplo)
            self.version_btn.setText("Não foi possível verificar agora")
            QTimer.singleShot(5000, self._reset_version_btn)

    def _show_update(self, upd: updater.UpdateInfo) -> None:
        self.update_info = upd
        auto = getattr(sys, "frozen", False) and upd.can_auto_install
        self.update_text.setText(f"Nova versão {upd.version} disponível!")
        self.update_btn.setText("Atualizar" if auto else "Ver novidades")
        self.update_btn.setEnabled(True)
        self.update_later.show()
        self.update_banner.show()
        self._fit_stack()

    def _hide_update_banner(self) -> None:
        self.update_banner.hide()
        self._fit_stack()

    def on_update(self) -> None:
        upd = self.update_info
        if not upd:
            return
        if not (getattr(sys, "frozen", False) and upd.can_auto_install):
            QDesktopServices.openUrl(QUrl(upd.page_url))  # versão pelo código ou sem checksum: abre a página
            return
        if self.task and self.task.isRunning():
            self.update_text.setText("Termine o download atual antes de atualizar.")
            return
        self.update_btn.setEnabled(False)
        self.update_later.hide()
        self.update_text.setText("Baixando a atualização… 0%")
        folder = Path.home() / "Downloads" if sys.platform.startswith("linux") else Path(tempfile.gettempdir())
        dest = folder / upd.asset_name
        self.update_cancel = threading.Event()
        cancel = self.update_cancel

        def work(task: Task):
            return str(
                updater.download(upd.asset_url, dest, upd.sha256, lambda d, t: task.progress.emit((d, t)), cancel)
            )

        task = self._keep(Task(work, self))
        task.progress.connect(self._on_update_progress)
        task.finished_ok.connect(self._on_update_downloaded)
        task.failed.connect(self._on_update_failed)
        task.start()

    def _on_update_progress(self, pair) -> None:
        done, total = pair
        pct = f"{int(done * 100 / total)}%" if total else core.fmt_size(done)
        self.update_text.setText(f"Baixando a atualização… {pct}")
        self._fit_stack()

    def _on_update_downloaded(self, path: str) -> None:
        if sys.platform.startswith("win"):
            self.update_text.setText("Instalador aberto. O TeaserTube vai fechar para atualizar.")
            os.startfile(path)  # type: ignore[attr-defined]
            QTimer.singleShot(1500, QApplication.quit)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
            self.update_text.setText("Abra o instalador e arraste o TeaserTube para Aplicativos, substituindo o atual.")
        else:
            open_folder(str(Path(path).parent))
            self.update_text.setText(f"Baixado em {Path(path).parent}. Extraia o arquivo e substitua o app atual.")
        self._fit_stack()

    def _on_update_failed(self, msg: str) -> None:
        self.update_text.setText((msg or "Não foi possível atualizar.") + " Abra a página para baixar à mão.")
        if self.update_info:
            self.update_info.sha256 = None  # o botão passa a abrir a página da release
        self.update_btn.setText("Abrir página")
        self.update_btn.setEnabled(True)
        self.update_later.show()
        self._fit_stack()

    def closeEvent(self, event) -> None:
        self.update_cancel.set()
        self.cancel.set()
        if self.task and self.task.isRunning():
            self.task.wait(3000)
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setDesktopFileName("teasertube")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setWindowIcon(svg_icon("icon.svg"))
    win = MainWindow()
    win.show()
    QTimer.singleShot(1500, win._check_updates)  # em segundo plano; falha em silêncio sem internet
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
