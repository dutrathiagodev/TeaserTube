"""Lógica de download (yt-dlp). Não depende da interface gráfica."""
from __future__ import annotations

import os
import re
import shutil
import threading
from dataclasses import dataclass, field
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


@dataclass
class Progress:
    stage: str
    percent: Optional[float] = None  # 0-100, None = indeterminado
    detail: str = ""


@dataclass
class Result:
    files: list[str]
    failed: int = 0
    folder: str = ""


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
    for name in ("deno", "node", "bun"):
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
    if "not a bot" in low or "sign in to confirm" in low:
        return "O YouTube pediu confirmação de que você não é um robô. Tente novamente mais tarde."
    if "private video" in low:
        return "Este vídeo é privado."
    if "video unavailable" in low or "this video is not available" in low:
        return "Vídeo indisponível."
    if "unsupported url" in low:
        return "Esse link não é suportado."
    if "urlopen error" in low or "unable to download" in low and "network" in low:
        return "Sem conexão com a internet."
    return msg.splitlines()[0] if msg else "Erro desconhecido."


def _thumb(info: dict) -> Optional[str]:
    thumbs = info.get("thumbnails") or []
    for t in reversed(thumbs):
        url = t.get("url") or ""
        if ".jpg" in url and (t.get("width") or 0) <= 900:
            return url
    return info.get("thumbnail") or (thumbs[-1].get("url") if thumbs else None)


def _base_opts() -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "windowsfilenames": True,
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
        }
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info.get("_type") == "playlist":
        entries = []
        for i, e in enumerate(info.get("entries") or [], start=1):
            if not e:
                continue
            entries.append(Entry(i, e.get("title") or f"Vídeo {i}", e.get("duration")))
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

    heights = sorted(
        {
            int(f["height"])
            for f in info.get("formats") or []
            if f.get("height") and f.get("vcodec") not in (None, "none")
        },
        reverse=True,
    )
    return MediaInfo(
        url=url,
        kind="video",
        title=info.get("title") or "Sem título",
        uploader=info.get("uploader") or info.get("channel") or "",
        duration=info.get("duration"),
        thumbnail=_thumb(info),
        heights=heights,
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
        opts["format_sort"] = ["res", "ext:mp4:m4a"]
        opts["merge_output_format"] = "mp4"

    total_items = len(order)
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
            bits = [_fmt_bytes(d.get("speed")) + "/s" if d.get("speed") else ""]
            if d.get("eta") is not None:
                bits.append(f"faltam {int(d['eta'])}s")
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

    opts["progress_hooks"] = [hook]
    opts["postprocessor_hooks"] = [pp_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.add_post_hook(files.append)
            ydl.download([info.url])
    except Exception as exc:
        if cancel.is_set() or isinstance(exc, Cancelled):
            raise Cancelled() from exc
        raise
    if cancel.is_set():
        raise Cancelled()

    failed = max(0, total_items - len(files))
    if not files:
        raise RuntimeError("Nenhum arquivo foi baixado.")
    folder = os.path.dirname(files[0]) if files else outdir
    return Result(files=files, failed=failed, folder=folder)
