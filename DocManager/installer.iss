; DocManager 安装脚本 (Inno Setup)

[Setup]
AppName=DocManager
AppVersion=1.0.0
AppPublisher=DocManager
AppPublisherURL=https://docmanager.app
DefaultDirName={autopf}\DocManager
DefaultGroupName=DocManager
OutputDir=installer
OutputBaseFilename=DocManager-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\DocManager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DocManager"; Filename: "{app}\DocManager.exe"
Name: "{group}\卸载 DocManager"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DocManager"; Filename: "{app}\DocManager.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DocManager.exe"; Description: "{cm:LaunchProgram,DocManager}"; Flags: nowait postinstall skipifsilent