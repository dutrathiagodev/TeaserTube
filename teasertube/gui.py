"""Interface gráfica (PySide6): cola o link, escolhe as opções e baixa."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSettings, QSize, Qt, QThread, Signal
from PySide6.QtGui import (
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

from . import core

APP_NAME = "TeaserTube"
ASSETS = Path(__file__).parent / "assets"

BG = QColor("#0b0b0d")
GLOW = QColor("#26262b")
LINE = QColor(170, 170, 180, 190)
YELLOW = "#FFD60A"

QUALITIES = ["Melhor qualidade", "1080p", "720p", "480p", "360p"]

STYLE = f"""
* {{ font-family: "Inter", "Segoe UI", "Ubuntu", "Helvetica Neue", Arial, sans-serif; }}
QLabel {{ color: #f4f4f5; background: transparent; }}
#card {{ background: #15151a; border: 1px solid #2c2c35; border-radius: 22px; }}
#subtitle, #muted {{ color: #9a9aa6; }}
#title {{ font-size: 24px; font-weight: 700; color: #ffffff; }}
#bigTitle {{ font-size: 20px; font-weight: 700; }}
#error {{ color: #ff6b6b; }}
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
QComboBox QAbstractItemView {{ background: #1f1f26; color: #f4f4f5; border: 1px solid #2c2c35;
            selection-background-color: {YELLOW}; selection-color: #111; outline: none; padding: 4px; }}
QProgressBar {{ background: #26262e; border: none; border-radius: 6px; height: 12px; }}
QProgressBar::chunk {{ background: {YELLOW}; border-radius: 6px; }}
QListWidget {{ background: #1a1a20; border: 1px solid #2c2c35; border-radius: 12px; color: #e4e4e7;
              padding: 4px; outline: none; font-size: 13px; }}
QListWidget::item {{ padding: 5px 4px; border-radius: 6px; }}
QListWidget::item:hover {{ background: #24242c; }}
QListWidget::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid #55555f;
              background: #1f1f26; }}
QListWidget::indicator:checked {{ background: {YELLOW}; border-color: {YELLOW}; }}
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
    return str(app_root() / "downloads")


def open_folder(path: str) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


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
        """A altura do cartão acompanha só a página visível."""
        for i in range(self.stack.count()):
            current = i == self.stack.currentIndex()
            self.stack.widget(i).setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Preferred if current else QSizePolicy.Ignored
            )
        self.card.adjustSize()

    def _show(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(page)
        self._fit_stack()

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
        self.quality.setMinimumWidth(190)
        fmt_row.addWidget(self.quality)
        fmt_row.addStretch(1)
        lay.addLayout(fmt_row)

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
        lay.setSpacing(12)
        self.res_icon = label("", align=Qt.AlignHCenter)
        self.res_icon.setStyleSheet(f"font-size:44px; font-weight:700; color:{YELLOW};")
        lay.addWidget(self.res_icon)
        self.res_title = label("", "bigTitle", align=Qt.AlignHCenter)
        lay.addWidget(self.res_title)
        self.res_msg = label("", "muted", wrap=True, align=Qt.AlignHCenter)
        lay.addWidget(self.res_msg)
        lay.addSpacing(8)
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
            if info.thumbnail:
                try:
                    req = urllib.request.Request(info.thumbnail, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        image.loadFromData(r.read())
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
        self._show(self.p_options)

    def _fill_qualities(self) -> None:
        self.quality.clear()
        if self.btn_audio.isChecked():
            self.quality.addItem("MP3 · 192 kbps")
            self.quality.setEnabled(False)
            return
        self.quality.setEnabled(True)
        self.quality.addItem("Melhor qualidade", None)
        if self.info and self.info.kind == "video" and self.info.heights:
            for h in self.info.heights:
                if h >= 144:
                    self.quality.addItem(f"{h}p", h)
        else:
            for h in (1080, 720, 480, 360):
                self.quality.addItem(f"{h}p", h)
        if self.quality.count() > 1:
            self.quality.setCurrentIndex(0)

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
        self.res_icon.setText("✓")
        self.res_icon.setStyleSheet(f"font-size:44px; font-weight:700; color:{YELLOW};")
        self.res_title.setText("Download concluído!")
        n = len(result.files)
        text = os.path.basename(result.files[0]) if n == 1 else f"{n} arquivos salvos"
        if result.failed:
            text += f"\n{result.failed} vídeo(s) não puderam ser baixados."
        self.res_msg.setText(text + f"\n{result.folder}")
        self.res_open.show()
        self.res_again.setText("Baixar outro")
        self._show(self.p_result)

    def _on_fail(self, msg: str) -> None:
        if not msg:  # cancelado
            self._show(self.p_options)
            return
        self.result = None
        self.res_icon.setText("✕")
        self.res_icon.setStyleSheet("font-size:44px; font-weight:700; color:#ff6b6b;")
        self.res_title.setText("Algo deu errado")
        self.res_msg.setText(msg)
        self.res_open.hide()
        self.res_again.setText("Voltar")
        self._show(self.p_result)

    def closeEvent(self, event) -> None:
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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
