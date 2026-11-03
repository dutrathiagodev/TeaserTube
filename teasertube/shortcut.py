"""Cria o atalho "TeaserTube" (com logo e nome) na área de trabalho.

Roda sozinho na primeira vez que o launcher é aberto. Para recriar:
    python -m teasertube.shortcut
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

NAME = "TeaserTube"
COMMENT = "Baixador de vídeos e áudios"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(__file__).resolve().parent / "assets"


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def desktop_dir() -> Path:
    if sys.platform.startswith("win"):
        out = _run(
            ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"]
        )
        if out:
            return Path(out)
    elif sys.platform.startswith("linux"):
        out = _run(["xdg-user-dir", "DESKTOP"])
        if out and Path(out) != Path.home():
            return Path(out)
    return Path.home() / "Desktop"


def _make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _windows(desktop: Path) -> Path:
    lnk = desktop / f"{NAME}.lnk"
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    script = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:TT_LNK);"
        "$s.TargetPath=$env:TT_EXE;$s.Arguments='-m teasertube';"
        "$s.WorkingDirectory=$env:TT_ROOT;$s.IconLocation=$env:TT_ICON;"
        "$s.Description=$env:TT_DESC;$s.Save()"
    )
    env = dict(
        os.environ,
        TT_LNK=str(lnk),
        TT_EXE=str(pythonw if pythonw.exists() else sys.executable),
        TT_ROOT=str(ROOT),
        TT_ICON=str(ASSETS / "icon.ico"),
        TT_DESC=COMMENT,
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", script], env=env, check=True)
    return lnk


def _linux(desktop: Path) -> Path:
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={NAME}\n"
        f"Comment={COMMENT}\n"
        f'Exec="{sys.executable}" -m teasertube\n'
        f"Path={ROOT}\n"
        f"Icon={ASSETS / 'icon.png'}\n"
        "Terminal=false\n"
        "Categories=AudioVideo;Network;\n"
        "StartupNotify=true\n"
    )
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    desktop.mkdir(parents=True, exist_ok=True)
    menu_file = apps / "teasertube.desktop"
    desk_file = desktop / f"{NAME}.desktop"
    for f in (menu_file, desk_file):
        f.write_text(entry, encoding="utf-8")
        _make_executable(f)
    _run(["gio", "set", str(desk_file), "metadata::trusted", "true"])  # GNOME: permite abrir
    _run(["update-desktop-database", str(apps)])
    return desk_file


def _macos(desktop: Path) -> Path:
    app = desktop / f"{NAME}.app"
    macos_dir = app / "Contents" / "MacOS"
    res_dir = app / "Contents" / "Resources"
    macos_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)
    launcher = macos_dir / NAME
    launcher.write_text(
        f'#!/bin/bash\ncd "{ROOT}"\nexec "{sys.executable}" -m teasertube\n', encoding="utf-8"
    )
    _make_executable(launcher)
    (res_dir / "icon.icns").write_bytes((ASSETS / "icon.icns").read_bytes())
    (app / "Contents" / "Info.plist").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        f"<key>CFBundleName</key><string>{NAME}</string>\n"
        f"<key>CFBundleDisplayName</key><string>{NAME}</string>\n"
        f"<key>CFBundleExecutable</key><string>{NAME}</string>\n"
        "<key>CFBundleIconFile</key><string>icon</string>\n"
        "<key>CFBundleIdentifier</key><string>com.teasertube.app</string>\n"
        "<key>CFBundlePackageType</key><string>APPL</string>\n"
        "<key>NSHighResolutionCapable</key><true/>\n"
        "</dict></plist>\n",
        encoding="utf-8",
    )
    _run(["touch", str(app)])  # atualiza o ícone no Finder
    return app


def create_desktop_shortcut() -> Path:
    desktop = desktop_dir()
    if sys.platform.startswith("win"):
        return _windows(desktop)
    if sys.platform == "darwin":
        return _macos(desktop)
    return _linux(desktop)


def main() -> None:
    try:
        path = create_desktop_shortcut()
        print(f"Atalho criado: {path}")
    except Exception as exc:  # noqa: BLE001
        print(f"Não foi possível criar o atalho: {exc}")


if __name__ == "__main__":
    main()
