#!/usr/bin/env bash
# Inicia o TeaserTube (Linux e macOS).
# Na primeira vez prepara tudo sozinho e cria o atalho na área de trabalho.
cd "$(dirname "$0")" || exit 1
VENV=".venv"

aviso() {
    echo "$1"
    command -v notify-send >/dev/null 2>&1 && notify-send "TeaserTube" "$1"
}

falha() {
    aviso "$1"
    [ -t 0 ] && read -r -p "Pressione Enter para fechar..."
    exit 1
}

if [ ! -x "$VENV/bin/python" ]; then
    PY="$(command -v python3 || command -v python)"
    [ -z "$PY" ] && falha "Python 3.9 ou mais novo não encontrado. Instale em https://www.python.org/downloads/"
    aviso "Preparando o TeaserTube pela primeira vez, aguarde..."
    "$PY" -m venv "$VENV" || falha "Não foi possível criar o ambiente. No Debian/Ubuntu: sudo apt install python3-venv"
fi

if [ ! -f "$VENV/.instalado" ]; then
    echo "Instalando componentes (só na primeira vez)..."
    "$VENV/bin/python" -m pip install --quiet --upgrade pip
    "$VENV/bin/python" -m pip install --quiet -r requirements.txt \
        || falha "Falha ao instalar. Verifique a internet e tente de novo."
    touch "$VENV/.instalado"
    "$VENV/bin/python" -m teasertube.shortcut
fi

nohup "$VENV/bin/python" -m teasertube >/dev/null 2>&1 &
