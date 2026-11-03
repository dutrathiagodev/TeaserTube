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

Requer Python 3.9 ou mais novo (no Windows, marque "Add Python to PATH" ao instalar).
Baixe ou clone o repositório e dê **dois cliques** no launcher do seu sistema:

| Sistema | Arquivo |
|---------|---------|
| Windows | `TeaserTube.bat` |
| macOS   | `TeaserTube.app` (já vem com o ícone) |
| Linux   | `TeaserTube.sh` (ou `./TeaserTube.sh` no terminal) |

Na **primeira vez** ele cria o ambiente, instala as dependências (leva um minuto) e coloca
um atalho **TeaserTube**, com o logo, na sua área de trabalho. Depois é só abrir pelo atalho.

- Se mudar a pasta do projeto de lugar, recrie o atalho com `python -m teasertube.shortcut`
  (usando o Python do `.venv`).
- No Linux, se o clique duplo no `.sh` abrir um editor, ajuste o gerenciador de arquivos para
  "executar arquivos de texto" ou rode `./TeaserTube.sh` uma vez no terminal.
- Se a janela não abrir no Linux com erro do Qt `xcb`: `sudo apt install libxcb-cursor0`.

### Manualmente

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m teasertube
```

## App com ícone para Windows, macOS e Linux (sem precisar de Python)

O workflow `.github/workflows/release.yml` gera o `TeaserTube.exe`, o `TeaserTube.app` e o binário Linux,
todos com o ícone. Crie uma tag (`git tag v0.1.0 && git push --tags`) ou rode o workflow em
*Actions > Release > Run workflow*; os arquivos aparecem nos Releases do GitHub.

## Gerar executável manualmente

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name TeaserTube --icon teasertube/assets/icon.png --add-data "teasertube/assets:teasertube/assets" --collect-all imageio_ffmpeg --collect-all deno --collect-all yt_dlp_ejs run_teasertube.py
```

No Windows, troque `:` por `;` em `--add-data`. O resultado fica em `dist/`.

## Aviso legal

Baixe apenas conteúdo que você tem direito de baixar. Respeite os direitos autorais
e os termos de uso das plataformas. O autor não se responsabiliza pelo uso da ferramenta.

## Licença

MIT
