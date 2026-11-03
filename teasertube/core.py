"""Lógica de download (yt-dlp). Não depende da interface gráfica."""
from __future__ import annotations

import os
import re
import shutil
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

import yt_dlp

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Cancelled(Exception):
    """Download cancelado pelo usuário."""


@dataclass
class Entry:
    index: int  # posição na playlist (começa em 1)
    title: str
    duration: Optional[int] = None
    id: str = ""


@dataclass
class MediaInfo:
    url: str
    kind: str  # "video" | "playlist"
    title: str
    uploader: str = ""
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    heights: list[int] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)
    # Link só do vídeo quando a URL colada é de um vídeo dentro de uma playlist.
    single_url: Optional[str] = None
    # Tamanho estimado em bytes do vídeo de cada altura e do melhor áudio (vazio se desconhecido).
    sizes: dict[int, int] = field(default_factory=dict)
    audio_size: int = 0
    best_size: int = 0  # tamanho total (vídeo + áudio) da opção "melhor qualidade"
    live_status: Optional[str] = None  # "is_live", "is_upcoming", "was_live", "not_live"

    @property
    def is_ongoing(self) -> bool:
        """Live no ar ou ainda por começar: não dá para baixar uma gravação completa."""
        return self.live_status in ("is_live", "is_upcoming")


@dataclass
class Progress:
    stage: str
    percent: Optional[float] = None  # 0-100, None = indeterminado
    detail: str = ""


@dataclass
class Failure:
    title: str
    reason: str


@dataclass
class Result:
    files: list[str]
    failures: list[Failure] = field(default_factory=list)
    folder: str = ""

    @property
    def failed(self) -> int:
        return len(self.failures)


# --------------------------------------------------------------------------- #
# Ferramentas externas (ffmpeg / runtime JS)
# --------------------------------------------------------------------------- #
def find_ffmpeg() -> Optional[str]:
    """ffmpeg do sistema, ou o binário embutido no pacote imageio-ffmpeg."""
    if shutil.which("ffmpeg"):
        return None  # yt-dlp encontra sozinho
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def has_ffmpeg() -> bool:
    return bool(shutil.which("ffmpeg") or find_ffmpeg())


def js_runtimes() -> dict:
    """Runtime JS usado pelo yt-dlp para decifrar o YouTube (deno, node ou bun)."""
    found: dict = {}
    bundle = getattr(sys, "_MEIPASS", None)  # app empacotado (PyInstaller)
    if bundle:
        for exe in ("deno", "deno.exe"):
            if (Path(bundle) / "bin" / exe).exists():
                found["deno"] = {"path": str(Path(bundle) / "bin" / exe)}
    for name in ("deno", "node", "bun"):
        if name in found:
            continue
        path = shutil.which(name)
        if path:
            found[name] = {"path": path}
    if not found:
        try:
            import deno

            found["deno"] = {"path": deno.find_deno_bin()}
        except Exception:
            pass
    return found


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def normalize_url(text: str) -> str:
    text = text.strip()
    if text and "://" not in text:
        text = "https://" + text
    return text


def _single_video_url(url: str) -> Optional[str]:
    """Se a URL aponta para um vídeo dentro de uma playlist, devolve só o vídeo."""
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if host == "youtu.be" and u.path.strip("/"):
        return f"https://www.youtube.com/watch?v={u.path.strip('/')}"
    vid = parse_qs(u.query).get("v")
    if vid:
        return f"https://www.youtube.com/watch?v={vid[0]}"
    return None


def clean_error(exc: BaseException) -> str:
    msg = _ANSI.sub("", str(exc)).strip()
    msg = re.sub(r"^(ERROR:\s*)+", "", msg)
    msg = re.sub(r"^\[[^\]]+\]\s*[\w-]{6,}:\s*", "", msg)
    low = msg.lower()
    rules = [
        (("confirm your age", "age-restricted", "inappropriate for some users"),
         "Vídeo com restrição de idade (exige login)."),
        (("not a bot", "sign in to confirm"),
         "O YouTube pediu confirmação de que você não é um robô. Tente novamente mais tarde."),
        (("private video", "video is private", "is private"), "Este vídeo é privado."),
        (("members-only", "join this channel"), "Vídeo exclusivo para membros do canal."),
        (("copyright",), "Bloqueado por direitos autorais."),
        (("not available in your country", "blocked it in your country"),
         "Não está disponível no seu país."),
        (("live event will begin", "premieres in"), "Transmissão ou estreia que ainda não começou."),
        (("deleted video",), "O vídeo foi apagado."),
        (("has been removed", "account associated", "no longer available"), "O vídeo foi removido."),
        (("unavailable",), "Vídeo indisponível."),
        (("unsupported url",), "Esse link não é suportado."),
        (("urlopen error", "name resolution", "network is unreachable", "timed out"),
         "Sem conexão com a internet."),
    ]
    for keys, text in rules:
        if any(k in low for k in keys):
            return text
    return msg.splitlines()[0] if msg else "Erro desconhecido."


def _thumb(info: dict) -> Optional[str]:
    thumbs = info.get("thumbnails") or []
    for t in reversed(thumbs):
        url = t.get("url") or ""
        if ".jpg" in url and (t.get("width") or 0) <= 900:
            return url
    return info.get("thumbnail") or (thumbs[-1].get("url") if thumbs else None)


FORMAT_SORT = ["res", "ext:mp4:m4a"]


def _format_size(f: dict, duration) -> int:
    n = f.get("filesize") or f.get("filesize_approx")
    if not n and f.get("tbr") and duration:
        n = f["tbr"] * 1000 / 8 * duration
    return int(n or 0)


def _chosen_sizes(ydl, info: dict) -> dict[Optional[int], int]:
    """Pergunta ao yt-dlp qual formato ele baixaria em cada altura e soma o tamanho (vídeo + áudio)."""
    import copy

    out: dict[Optional[int], int] = {}
    duration = info.get("duration")
    heights = {int(f["height"]) for f in info.get("formats") or [] if f.get("height") and f.get("vcodec") not in (None, "none")}
    saved = ydl.format_selector
    try:
        for h in [None, *sorted(heights)]:
            limit = f"[height<={h}]" if h else ""
            ydl.format_selector = ydl.build_format_selector(f"bv*{limit}+ba/b{limit}")
            try:
                res = ydl.process_video_result(copy.deepcopy(info), download=False)
            except Exception:  # noqa: BLE001
                continue
            parts = res.get("requested_formats") or [res]
            total = sum(_format_size(f, duration) for f in parts)
            if total:
                out[h] = total
    finally:
        ydl.format_selector = saved
    return out


def _base_opts() -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "windowsfilenames": True,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 3,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,  # vídeos longos vêm em milhares de pedaços
        "trim_file_name": 150,  # títulos de lives costumam estourar o limite do sistema
    }
    runtimes = js_runtimes()
    if runtimes:
        opts["js_runtimes"] = runtimes
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg
    return opts


# --------------------------------------------------------------------------- #
# Buscar informações
# --------------------------------------------------------------------------- #
def fetch_info(url: str, single: bool = False) -> MediaInfo:
    """Lê título, qualidades e (se for playlist) a lista de vídeos."""
    opts = _base_opts()
    opts.update(
        {
            "skip_download": True,
            "noplaylist": single,
            "extract_flat": "in_playlist",
            "playlist_items": "1:500",
            "format_sort": FORMAT_SORT,
        }
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        chosen = _chosen_sizes(ydl, info) if info.get("_type") != "playlist" else {}

    if info.get("_type") == "playlist":
        entries = []
        for i, e in enumerate(info.get("entries") or [], start=1):
            if not e:
                continue
            entries.append(Entry(i, e.get("title") or f"Vídeo {i}", e.get("duration"), e.get("id") or ""))
        thumb = _thumb(info)
        if not thumb:
            first = next((e for e in info.get("entries") or [] if e), None)
            thumb = _thumb(first) if first else None
        return MediaInfo(
            url=url,
            kind="playlist",
            title=info.get("title") or "Playlist",
            uploader=info.get("uploader") or info.get("channel") or "",
            thumbnail=thumb,
            entries=entries,
            single_url=_single_video_url(url),
        )

    formats = info.get("formats") or []
    duration = info.get("duration")

    def size_of(f: dict) -> int:
        n = f.get("filesize") or f.get("filesize_approx")
        if not n and f.get("tbr") and duration:
            n = f["tbr"] * 1000 / 8 * duration
        return int(n or 0)

    # O app prefere MP4 (vídeo) e M4A (áudio): estima pelo formato que será realmente baixado.
    by_height: dict[int, list[tuple[bool, int]]] = {}
    audios: list[tuple[bool, int]] = []
    for f in formats:
        if f.get("vcodec") not in (None, "none") and f.get("height"):
            by_height.setdefault(int(f["height"]), []).append((f.get("ext") == "mp4", size_of(f)))
        elif f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none"):
            audios.append((f.get("ext") == "m4a", size_of(f)))

    def pick(options: list[tuple[bool, int]]) -> int:
        preferred = [n for ok, n in options if ok and n]
        return max(preferred) if preferred else max((n for _, n in options), default=0)

    audio_size = pick(audios)
    # Reserva (se o yt-dlp não conseguiu simular a escolha): maior MP4 da altura + áudio.
    sizes = {h: pick(opts) + audio_size for h, opts in by_height.items() if pick(opts)}
    sizes.update({h: n for h, n in chosen.items() if h is not None})
    best_total = chosen.get(None, 0)
    heights = sorted(sizes, reverse=True)
    return MediaInfo(
        url=url,
        kind="video",
        title=info.get("title") or "Sem título",
        uploader=info.get("uploader") or info.get("channel") or "",
        duration=info.get("duration"),
        thumbnail=_thumb(info),
        heights=heights,
        sizes={h: n for h, n in sizes.items() if n},
        best_size=best_total,
        audio_size=audio_size,
        live_status=info.get("live_status"),
    )


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
def _fmt_bytes(n: Optional[float]) -> str:
    if not n:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return ""


class _Log:
    """Logger do yt-dlp: guarda só os erros (para dizer qual vídeo falhou e por quê)."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        self.errors.append(str(msg))


_PERMANENT = (
    "privado", "removido", "apagado", "membros", "direitos autorais", "país", "idade", "não começou",
)

_VIDEO_ID = re.compile(r"\[[\w:]+\]\s+([\w-]{11}):")


def _failures(errors: list[str], info: MediaInfo) -> list[Failure]:
    titles = {e.id: e.title for e in info.entries if e.id}
    seen, out = set(), []
    for msg in errors:
        m = _VIDEO_ID.search(_ANSI.sub("", msg))
        vid = m.group(1) if m else ""
        reason = clean_error(Exception(msg))
        key = (vid, reason)
        if key in seen:
            continue
        seen.add(key)
        out.append(Failure(titles.get(vid) or (f"Vídeo {vid}" if vid else "Vídeo desconhecido"), reason))
    return out


def fmt_size(n: Optional[float]) -> str:
    """Tamanho legível em português: 1,5 GB."""
    if not n:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return (f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}").replace(".", ",")
        n /= 1024
    return ""


def fmt_eta(seconds: Optional[float]) -> str:
    if seconds is None:
        return ""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}h{m:02d}min" if h else (f"{m}min{sec:02d}s" if m else f"{sec}s")


def estimate_bytes(info: MediaInfo, mode: str, height: Optional[int]) -> int:
    """Tamanho final estimado em bytes (0 = desconhecido)."""
    if info.kind != "video":
        return 0
    if mode == "audio":
        return int((info.duration or 0) * 192_000 / 8) or info.audio_size
    if not info.sizes:
        return 0
    if height is None:
        return info.best_size or info.sizes[max(info.sizes)]
    fits = [h for h in info.sizes if h <= height]
    return info.sizes[max(fits)] if fits else min(info.sizes.values())


def disk_needed(estimate: int) -> int:
    """Espaço livre necessário: durante a junção de vídeo e áudio o disco guarda tudo duas vezes."""
    return int(estimate * 2.1)


def download(
    info: MediaInfo,
    mode: str,  # "video" | "audio"
    height: Optional[int],  # None = melhor qualidade
    outdir: str,
    selected: Optional[list[int]],  # índices da playlist (1-based)
    on_progress: Callable[[Progress], None],
    cancel: threading.Event,
) -> Result:
    is_playlist = info.kind == "playlist"
    ffmpeg_ok = has_ffmpeg()
    if mode == "audio" and not ffmpeg_ok:
        raise RuntimeError("Converter para MP3 precisa do ffmpeg (instale-o ou reinstale o app).")

    opts = _base_opts()
    opts["noplaylist"] = not is_playlist
    opts["paths"] = {"home": outdir}
    if is_playlist:
        opts["outtmpl"] = "%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"
        opts["ignoreerrors"] = True
        if selected:
            opts["playlist_items"] = ",".join(str(i) for i in selected)
        order = sorted(selected) if selected else [e.index for e in info.entries]
    else:
        opts["outtmpl"] = "%(title)s.%(ext)s"
        order = [1]

    if mode == "audio":
        opts["format"] = "ba/b"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    elif not ffmpeg_ok:
        opts["format"] = "b[ext=mp4]/b"
    else:
        limit = f"[height<={height}]" if height else ""
        opts["format"] = f"bv*{limit}+ba/b{limit}"
        opts["format_sort"] = FORMAT_SORT
        opts["merge_output_format"] = "mp4"

    total_items = total_all = len(order)
    streams_done: dict[int, int] = {}
    files: list[str] = []

    def position(d: dict) -> tuple[int, int]:
        """(ordem do item na fila, índice da playlist)"""
        pi = (d.get("info_dict") or {}).get("playlist_index") or 1
        return (order.index(pi) if pi in order else 0), pi

    def label(d: dict) -> str:
        pos, _ = position(d)
        title = (d.get("info_dict") or {}).get("title") or ""
        if is_playlist:
            return f"Vídeo {pos + 1} de {total_items}" + (f" · {title}" if title else "")
        return "Baixando…"

    def hook(d: dict) -> None:
        if cancel.is_set():
            raise Cancelled()
        pos, pi = position(d)
        n_streams = len((d.get("info_dict") or {}).get("requested_formats") or [1])
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            frac = (d.get("downloaded_bytes") or 0) / total if total else 0
            overall = (pos + (streams_done.get(pi, 0) + frac) / n_streams) / total_items
            bits = []
            if total:
                bits.append(f"{fmt_size(d.get('downloaded_bytes') or 0)} de {fmt_size(total)}")
            if d.get("speed"):
                bits.append(f"{fmt_size(d['speed'])}/s")
            if d.get("eta") is not None:
                bits.append(f"faltam {fmt_eta(d['eta'])}")
            on_progress(Progress(label(d), overall * 100, "  ·  ".join(b for b in bits if b)))
        elif d["status"] == "finished":
            streams_done[pi] = streams_done.get(pi, 0) + 1

    def pp_hook(d: dict) -> None:
        if cancel.is_set():
            raise Cancelled()
        if d["status"] == "started":
            names = {"Merger": "Juntando vídeo e áudio…", "ExtractAudio": "Convertendo para MP3…"}
            pos, _ = position(d)
            on_progress(Progress(label(d), None, names.get(d["postprocessor"], "Finalizando…")))

    log = _Log()
    opts["logger"] = log
    opts["progress_hooks"] = [hook]
    opts["postprocessor_hooks"] = [pp_hook]

    def run(items: Optional[list[int]]) -> None:
        run_opts = dict(opts)
        if items:
            run_opts["playlist_items"] = ",".join(str(i) for i in items)
        try:
            with yt_dlp.YoutubeDL(run_opts) as ydl:
                ydl.add_post_hook(files.append)
                ydl.download([info.url])
        except Exception as exc:
            if cancel.is_set() or isinstance(exc, Cancelled):
                raise Cancelled() from exc
            raise
        if cancel.is_set():
            raise Cancelled()

    run(selected if is_playlist else None)
    failures = _failures(log.errors, info)

    if is_playlist and failures:
        # Falhas passageiras (conexão, 403...) costumam passar na segunda tentativa.
        by_title = {e.title: e.index for e in info.entries}
        retryable = {
            f.title: by_title[f.title]
            for f in failures
            if f.title in by_title and not any(k in f.reason for k in _PERMANENT)
        }
        if retryable:
            on_progress(Progress("Tentando de novo os vídeos que falharam…", None, ""))
            order[:] = list(retryable.values())
            total_items = len(order)
            streams_done.clear()
            log.errors.clear()
            run(order)
            failures = [f for f in failures if f.title not in retryable] + _failures(log.errors, info)

    if cancel.is_set():
        raise Cancelled()
    if not files:
        raise RuntimeError(failures[0].reason if failures else "Nenhum arquivo foi baixado.")
    missing = total_all - len(files) - len(failures)
    if missing > 0:  # falhou sem mensagem de erro
        failures.append(Failure(f"{missing} vídeo(s)", "Não foi possível baixar."))
    return Result(files=files, failures=failures, folder=os.path.dirname(files[0]))
