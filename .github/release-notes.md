## TeaserTube

Baixe vídeos e playlists do YouTube em **MP4** ou só o áudio em **MP3**, com uma interface simples: cole o link, escolha o formato e clique em Baixar.

### Qual arquivo baixar

| Seu sistema | Arquivo | Como abrir |
|-------------|---------|------------|
| Windows 10 ou 11 (64 bits) | `TeaserTube-windows-x64.zip` | Extraia o zip e abra `TeaserTube.exe` |
| Mac com chip Apple (M1, M2, M3...) | `TeaserTube-macos-apple-silicon.zip` | Extraia e abra `TeaserTube.app` |
| Mac com processador Intel | `TeaserTube-macos-intel.zip` | Extraia e abra `TeaserTube.app` |
| Linux 64 bits (Intel/AMD) | `TeaserTube-linux-x64.tar.gz` | Extraia e execute `TeaserTube/TeaserTube` |
| Linux ARM64 (Raspberry Pi 4/5, Mac com Asahi...) | `TeaserTube-linux-arm64.tar.gz` | Extraia e execute `TeaserTube/TeaserTube` |

Não sabe qual Mac você tem? Menu  > *Sobre este Mac*: se aparecer "Chip Apple", é o de Apple Silicon.
Os arquivos **Source code (zip / tar.gz)** no fim da página são só o código-fonte; não precisa deles para usar o app.

### Antes de abrir

- **Extraia tudo primeiro.** O app precisa dos arquivos que vêm na mesma pasta; abrir de dentro do zip não funciona.
- **Windows:** o app não é assinado, então o SmartScreen pode avisar. Clique em *Mais informações* e depois em *Executar assim mesmo*.
- **macOS:** clique com o botão direito no app e escolha *Abrir* na primeira vez.
- **Linux:** funciona nas distribuições de 2020 em diante (Ubuntu 20.04+, Debian 11+, Fedora, Arch, openSUSE, Linux Mint, Pop!_OS...). Se não abrir, instale a biblioteca gráfica que falta: `sudo apt install libxcb-cursor0` (Debian/Ubuntu) ou `sudo dnf install xcb-util-cursor` (Fedora).
- **Outros sistemas** (Windows 7/8, sistemas 32 bits, BSD): o Qt atual não roda neles. Se você tem Python 3.9+, dá para usar pelo código; veja o README.

### O que ele faz

- Vídeo em MP4 (melhor qualidade, 1080p, 720p, 480p ou 360p) ou áudio em MP3
- Playlists: escolha quais vídeos baixar; cada playlist vai para a própria pasta
- Mostra qual vídeo falhou e por quê, e tenta de novo sozinho quando é falha passageira
- Não precisa instalar Python, ffmpeg nem mais nada

Dúvidas ou problemas? Abra uma [issue](https://github.com/dutrathiagodev/TeaserTube/issues).
