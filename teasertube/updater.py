"""Verifica se há uma versão nova no GitHub e baixa o instalador com conferência de checksum.

Só fala com a API pública do GitHub (nenhum dado seu é enviado). Para desligar a verificação
automática, defina a variável de ambiente TEASERTUBE_NO_UPDATE_CHECK=1.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import __version__

REPO = "dutrathiagodev/TeaserTube"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
ASSET_PREFIX = f"https://github.com/{REPO}/releases/download/"
SUMS_NAME = "SHA256SUMS.txt"


class UpdateError(Exception):
    """Falha ao verificar ou baixar a atualização."""


@dataclass
class UpdateInfo:
    version: str  # ex.: "0.1.3"
    page_url: str  # página da release
    asset_name: Optional[str] = None  # arquivo certo para este sistema
    asset_url: Optional[str] = None
    sha256: Optional[str] = None  # None = não dá para conferir: o app só abre a página

    @property
    def can_auto_install(self) -> bool:
        return bool(self.asset_url and self.sha256)


def parse_version(text: str) -> tuple[int, ...]:
    """'v0.1.10' -> (0, 1, 10). Sufixos como '-beta' são ignorados."""
    nums = re.findall(r"\d+", text.strip().lstrip("vV").split("-")[0])
    return tuple(int(n) for n in nums) or (0,)


def is_newer(remote: str, local: str = __version__) -> bool:
    return parse_version(remote) > parse_version(local)


def asset_for_this_system() -> Optional[str]:
    machine = platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    if sys.platform.startswith("win"):
        return "TeaserTube-windows-x64-setup.exe"
    if sys.platform == "darwin":
        return "TeaserTube-macos-apple-silicon.dmg" if arm else "TeaserTube-macos-intel.dmg"
    if sys.platform.startswith("linux"):
        return "TeaserTube-linux-arm64.tar.gz" if arm else "TeaserTube-linux-x64.tar.gz"
    return None


def _get(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": f"TeaserTube/{__version__}", "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(2_000_000)  # respostas de API são pequenas


def parse_sums(text: str) -> dict[str, str]:
    """Lê um SHA256SUMS.txt ('<hash>  <arquivo>') e devolve {arquivo: hash}."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if m:
            out[m.group(2)] = m.group(1).lower()
    return out


def check(timeout: float = 8.0, fetch: Callable[[str, float], bytes] = _get) -> Optional[UpdateInfo]:
    """Devolve os dados da versão nova, ou None se já está na mais recente."""
    try:
        data = json.loads(fetch(API_LATEST, timeout))
    except Exception as exc:  # noqa: BLE001
        raise UpdateError("Não foi possível falar com o GitHub.") from exc
    tag = str(data.get("tag_name") or "")
    if not tag or not is_newer(tag):
        return None

    info = UpdateInfo(version=tag.lstrip("vV"), page_url=data.get("html_url") or RELEASES_PAGE)
    assets = {a.get("name"): a.get("browser_download_url") for a in data.get("assets") or []}
    name = asset_for_this_system()
    url = assets.get(name) if name else None
    if url and url.startswith(ASSET_PREFIX):
        info.asset_name, info.asset_url = name, url
        sums_url = assets.get(SUMS_NAME)
        if sums_url and sums_url.startswith(ASSET_PREFIX):
            try:
                info.sha256 = parse_sums(fetch(sums_url, timeout).decode("utf-8", "replace")).get(name)
            except Exception:  # noqa: BLE001
                info.sha256 = None
    return info


def download(
    url: str,
    dest: Path,
    sha256: str,
    on_progress: Callable[[int, int], None],
    cancel: threading.Event,
    allowed_prefix: str = ASSET_PREFIX,
) -> Path:
    """Baixa o arquivo e só o mantém se o SHA-256 conferir."""
    if not url.startswith(allowed_prefix):
        raise UpdateError("Endereço de download inesperado; a atualização foi recusada.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    digest = hashlib.sha256()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"TeaserTube/{__version__}"})
        with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                if cancel.is_set():
                    raise UpdateError("Atualização cancelada.")
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                on_progress(done, total)
        if digest.hexdigest().lower() != sha256.lower():
            raise UpdateError("O arquivo baixado não confere com o checksum oficial; foi descartado.")
        tmp.replace(dest)
        return dest
    except UpdateError:
        tmp.unlink(missing_ok=True)
        raise
    except Exception as exc:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        raise UpdateError("Falha ao baixar a atualização.") from exc
