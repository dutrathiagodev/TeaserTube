# Segurança

## Como reportar um problema

Achou uma falha de segurança? **Não abra uma issue pública.** Use o botão
[Report a vulnerability](https://github.com/dutrathiagodev/TeaserTube/security/advisories/new)
(aba *Security* do repositório) para falar em privado. Respondo assim que possível.

## O que o TeaserTube faz (e não faz)

- Só se conecta à internet para falar com o site do vídeo (via [yt-dlp](https://github.com/yt-dlp/yt-dlp))
  e para baixar a miniatura (apenas `https`, no máximo 5 MB).
- Não coleta dados, não tem telemetria, não pede login nem senha.
- Grava arquivos só na pasta de downloads que você escolher.
- Textos vindos da internet (títulos dos vídeos) são sempre mostrados como texto puro, nunca como HTML.

## Como conferir que o download é legítimo

Os arquivos das releases são gerados automaticamente pelo GitHub Actions a partir deste repositório
(veja `.github/workflows/release.yml`); ninguém os monta à mão. Nas releases novas, cada versão traz:

- **`SHA256SUMS.txt`**: confira o seu arquivo com `sha256sum -c SHA256SUMS.txt` (Linux),
  `shasum -a 256 -c SHA256SUMS.txt` (macOS) ou `Get-FileHash arquivo` (Windows PowerShell).
- **Atestado de origem**: prova assinada de que o arquivo foi construído por este repositório.
  Com o [GitHub CLI](https://cli.github.com/): `gh attestation verify ARQUIVO --repo dutrathiagodev/TeaserTube`.

## Antivírus mostrou um alerta?

Programas empacotados com PyInstaller (como este) às vezes recebem **falsos positivos** de antivírus.
Se acontecer, confira o SHA-256 acima e, se quiser, reporte o falso positivo ao fabricante do antivírus.
O código é aberto e pode ser lido por inteiro neste repositório.
