<h1 align="center">
  <img src="teasertube/assets/icon.png" alt="TeaserTube" width="64" valign="middle" /> TeaserTube
</h1>

<p align="center">
  <a href="https://github.com/dutrathiagodev/TeaserTube"><img src="https://img.shields.io/github/stars/dutrathiagodev/TeaserTube?style=flat&label=%E2%98%85&color=FFD60A&labelColor=1b1b20" alt="Estrelas no GitHub" /></a>
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-FFD60A?style=flat&labelColor=1b1b20" alt="Licença MIT" />
  <img src="https://img.shields.io/badge/Windows%20%7C%20macOS%20%7C%20Linux-FFD60A?style=flat&labelColor=1b1b20" alt="Windows, macOS e Linux" />
  <img src="https://img.shields.io/badge/python-3.9%2B-FFD60A?style=flat&labelColor=1b1b20" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/feito%20com-yt--dlp-FFD60A?style=flat&labelColor=1b1b20" alt="Feito com yt-dlp" />
</p>

<p align="center">
  <strong>Baixe vídeos e playlists do YouTube em MP4 ou MP3.</strong><br/>
  Cole o link, escolha o formato e pronto. Open source, sem anúncios e sem instalar mais nada.
</p>

<h3 align="center"><a href="https://github.com/dutrathiagodev/TeaserTube/releases"><ins>Baixar o app</ins></a></h3>

<p align="center">
  <img src="docs/assets/home.png" alt="Tela inicial do TeaserTube" width="860" />
</p>

## Recursos

<table>
<tr>
<td width="46%" valign="middle">

### Vídeo ou só o áudio

MP4 na melhor qualidade ou em 1080p, 720p, 480p e 360p. Prefere música? Baixe em MP3 a 192 kbps.

</td>
<td width="54%">
  <img src="docs/assets/playlist.png" alt="Opções de formato e qualidade" width="100%" />
</td>
</tr>
<tr>
<td width="46%" valign="middle">

### Playlists do seu jeito

Marque só os vídeos que quiser. Cada playlist vai para a própria pasta, numerada na ordem certa. Colou um vídeo que está dentro de uma playlist? Um botão baixa só ele.

</td>
<td width="54%">
  <img src="docs/assets/progress.png" alt="Download de playlist em andamento" width="100%" />
</td>
</tr>
</table>

- **Nada para instalar além do Python:** o ffmpeg e o runtime JS vêm junto, como pacotes pip.
- **Vídeos longos e lives gravadas:** funciona com vídeos de várias horas. Mostra o tamanho estimado de cada qualidade, avisa antes de começar se o disco não tem espaço e baixa em partes simultâneas para ir mais rápido.
- **Progresso e cancelar:** acompanhe o quanto já baixou, a velocidade e o tempo restante.
- **Seus arquivos ficam à mão:** por padrão, na pasta `downloads/` do próprio app (dá para trocar).

<p align="center">
  <strong>⭐ O TeaserTube te salvou tempo?</strong><br/>
  Deixa uma estrela aqui no topo da página. É de graça, leva um segundo e deixa o dev muito feliz 😄
</p>

## Baixar o app pronto (sem Python)

Na página de [Releases](https://github.com/dutrathiagodev/TeaserTube/releases), baixe o arquivo do seu sistema:

| Sistema | Arquivo | Como instalar |
|---------|---------|---------------|
| Windows 10/11 (64 bits) | `TeaserTube-windows-x64-setup.exe` | Dê dois cliques e siga o instalador (não precisa de administrador) |
| Mac com chip Apple (M1 ou mais novo) | `TeaserTube-macos-apple-silicon.dmg` | Abra e arraste o TeaserTube para *Aplicativos* |
| Mac com processador Intel | `TeaserTube-macos-intel.dmg` | Abra e arraste o TeaserTube para *Aplicativos* |
| Linux 64 bits (Intel/AMD) | `TeaserTube-linux-x64.tar.gz` | Extraia e execute `TeaserTube/TeaserTube` |
| Linux ARM64 (Raspberry Pi etc.) | `TeaserTube-linux-arm64.tar.gz` | Extraia e execute `TeaserTube/TeaserTube` |

### O Windows mostrou uma tela azul ("O Windows protegeu o computador")?

Calma, é normal. É o **Microsoft Defender SmartScreen**, que aparece para qualquer programa novo que
ainda não tem assinatura digital, mesmo sendo seguro. O TeaserTube é open source: todo o código está
neste repositório e os arquivos são gerados automaticamente pelo GitHub Actions, sem passar pela máquina
de ninguém. Dois cliques resolvem (só na primeira vez):

<p align="center">
  <img src="docs/assets/smartscreen.png" alt="Passo a passo: clique em Mais informações e depois em Executar assim mesmo" width="860" />
</p>

1. Clique em **Mais informações**.
2. Clique em **Executar assim mesmo**.

> A imagem é uma ilustração; a tela do seu Windows pode ter pequenas diferenças.

### No Mac o sistema bloqueou o app?

Clique com o botão direito no TeaserTube (em *Aplicativos*) e escolha **Abrir**. Só na primeira vez.

### Linux

Os arquivos são compilados numa base antiga e abrem nas distribuições de 2020 em diante
(Ubuntu 20.04+, Debian 11+, Fedora, Arch, openSUSE, Mint...). Se não abrir, instale a biblioteca
gráfica que falta: `sudo apt install libxcb-cursor0` (Debian/Ubuntu) ou `sudo dnf install xcb-util-cursor` (Fedora).

**Outros sistemas** (Windows 7/8, sistemas 32 bits, BSD): o Qt atual não roda neles. Com Python 3.9+
dá para usar pelo código, veja abaixo.

## Como usar (pelo código)

Requer Python 3.9 ou mais novo (no Windows, marque "Add Python to PATH" ao instalar).
Baixe o ZIP do repositório (botão verde **Code**) ou clone:

```bash
git clone https://github.com/dutrathiagodev/TeaserTube.git
```

Depois dê **dois cliques** no launcher do seu sistema:

| Sistema | Arquivo |
|---------|---------|
| Windows | `TeaserTube.bat` |
| macOS   | `TeaserTube.app` |
| Linux   | `TeaserTube.sh` |

Na primeira vez ele prepara tudo (leva cerca de um minuto) e cria um atalho **TeaserTube**,
com o ícone, na sua área de trabalho. Depois é só abrir por ele.

<details>
<summary>Instalação manual e solução de problemas</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m teasertube
```

- Se mudar a pasta do projeto de lugar, recrie o atalho com `python -m teasertube.shortcut`.
- Linux: se o clique duplo no `.sh` abrir um editor, rode `./TeaserTube.sh` uma vez no terminal.
- Linux: erro do Qt `xcb` ao abrir? `sudo apt install libxcb-cursor0`.
- macOS: se o sistema bloquear o app na primeira vez, clique com o botão direito e escolha "Abrir".

</details>

<details>
<summary>Gerar o app com ícone (sem precisar de Python)</summary>

O workflow `.github/workflows/release.yml` gera o `.exe`, o `.app` e o binário Linux com o ícone.
Crie uma tag (`git tag v0.1.0 && git push --tags`) ou rode em *Actions > Release > Run workflow*;
os arquivos aparecem em *Releases*. Para empacotar na sua máquina:

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name TeaserTube --icon teasertube/assets/icon.png \
  --add-data "teasertube/assets:teasertube/assets" \
  --collect-all imageio_ffmpeg --collect-all deno --collect-all yt_dlp_ejs run_teasertube.py
```

No Windows, troque `:` por `;` em `--add-data` e use `--icon teasertube/assets/icon.ico`.

</details>

## Gostou? Dá uma estrela ⭐

Se o TeaserTube foi útil, [deixe uma estrela no repositório](https://github.com/dutrathiagodev/TeaserTube). Isso ajuda mais gente a encontrar o projeto
(e ajuda a conseguir, um dia, a assinatura digital que tira o aviso azul do Windows).

## Segurança

O código é aberto, os arquivos das releases são gerados pelo GitHub Actions e trazem checksums e atestado de origem.
Veja como conferir o seu download e como reportar um problema em [SECURITY.md](SECURITY.md).

## Contribuir

Pull requests são bem-vindos. O código fica em `teasertube/` (`core.py` cuida dos downloads,
`gui.py` da interface). Os scripts em `tools/` regeneram o logo, os ícones e as imagens deste README.

## Limitações

- **Lives que ainda estão no ar** não podem ser baixadas: o app avisa e pede para esperar a transmissão terminar para baixar a gravação.
- Em pen drives ou discos formatados como **FAT32**, arquivos acima de 4 GB não cabem; use um disco NTFS, exFAT, ext4 ou APFS.
- Vídeos de várias horas em 1080p ou mais ocupam muitos gigabytes; durante a junção de vídeo e áudio o espaço usado dobra.

## Aviso legal

Baixe apenas conteúdo que você tem direito de baixar e respeite os termos de uso das plataformas.
O autor não se responsabiliza pelo uso da ferramenta.

## Licença

[MIT](LICENSE)
