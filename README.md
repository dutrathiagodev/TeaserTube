# TeaserTube — baixador de vídeos e áudios

App de desktop (Windows, Linux e macOS) para baixar vídeos e playlists do YouTube
em **MP4** ou só o áudio em **MP3**. Cole o link, escolha as opções e clique em Baixar.

Feito com [yt-dlp](https://github.com/yt-dlp/yt-dlp) e PySide6.

## Recursos

- Vídeo (MP4, melhor qualidade ou 1080p/720p/480p/360p) ou áudio (MP3 192 kbps)
- Playlists: escolha quais vídeos baixar; cada playlist vai para sua própria subpasta
- Link de um vídeo dentro de uma playlist: botão para baixar só aquele vídeo
- Barra de progresso e botão de cancelar
- Nada para instalar além do Python: o ffmpeg e o runtime JS (Deno) vêm como pacotes pip
- Os downloads ficam em `downloads/`, na pasta do software (dá para trocar no botão "Alterar")

## Como usar

Requer Python 3.9 ou mais novo.

```bash
git clone <url-do-repositorio>
cd TeaserTube
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m teasertube
```

No Linux, se a janela não abrir com erro do Qt `xcb`, instale: `sudo apt install libxcb-cursor0`.

## Gerar executável (opcional)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name TeaserTube --add-data "teasertube/assets:teasertube/assets" teasertube/__main__.py
```

No Windows, troque `:` por `;` em `--add-data`. O resultado fica em `dist/`.

## Aviso legal

Baixe apenas conteúdo que você tem direito de baixar. Respeite os direitos autorais
e os termos de uso das plataformas. O autor não se responsabiliza pelo uso da ferramenta.

## Licença

MIT
