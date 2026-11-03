@echo off
setlocal
cd /d "%~dp0"
title TeaserTube

if not exist ".venv\Scripts\python.exe" (
    echo Preparando o TeaserTube pela primeira vez, aguarde...
    where py >nul 2>nul && (py -3 -m venv .venv) || (python -m venv .venv)
)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Python 3.9 ou mais novo nao encontrado.
    echo Instale em https://www.python.org/downloads/ marcando "Add Python to PATH".
    pause
    exit /b 1
)
if not exist ".venv\.instalado" (
    echo Instalando componentes, isso so acontece na primeira vez...
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo Falha ao instalar. Verifique a internet e tente de novo.
        pause
        exit /b 1
    )
    echo ok> ".venv\.instalado"
    ".venv\Scripts\python.exe" -m teasertube.shortcut
)
start "" ".venv\Scripts\pythonw.exe" -m teasertube
