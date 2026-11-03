; Instalador do Windows (Inno Setup). Gerado pelo workflow: iscc /DAppVersion=0.1.1 installer\TeaserTube.iss
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{DA2188F5-2D6C-40AB-B100-D7E4B6B78E4C}
AppName=TeaserTube
AppVersion={#AppVersion}
AppPublisher=TeaserTube
AppPublisherURL=https://github.com/dutrathiagodev/TeaserTube
AppSupportURL=https://github.com/dutrathiagodev/TeaserTube/issues
DefaultDirName={autopf}\TeaserTube
DefaultGroupName=TeaserTube
DisableProgramGroupPage=yes
; Instala só para o usuário atual: não pede senha de administrador.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..
OutputBaseFilename=TeaserTube-windows-x64-setup
SetupIconFile=..\teasertube\assets\icon.ico
UninstallDisplayIcon={app}\TeaserTube.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\dist\TeaserTube\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\TeaserTube"; Filename: "{app}\TeaserTube.exe"
Name: "{autodesktop}\TeaserTube"; Filename: "{app}\TeaserTube.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TeaserTube.exe"; Description: "Abrir o TeaserTube agora"; Flags: nowait postinstall skipifsilent
