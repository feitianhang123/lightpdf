[Setup]
AppId={{B2F5D0E1-7A3C-4E9B-9C21-8F4A6D2E1B33}
AppName=轻PDF编辑器
AppVersion=1.0.1
AppVerName=轻PDF编辑器 1.0.1
AppPublisher=轻PDF编辑器
DefaultDirName={autopf}\轻PDF编辑器
DefaultGroupName=轻PDF编辑器
DisableProgramGroupPage=yes
OutputDir=F:\自写软件\PDF编辑逆向软件\安装包
OutputBaseFilename=setup
SetupIconFile=F:\自写软件\PDF编辑逆向软件\icon.ico
UninstallDisplayIcon={app}\轻PDF编辑器.exe
UninstallDisplayName=轻PDF编辑器
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "F:\自写软件\PDF编辑逆向软件\dist\轻PDF编辑器.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "F:\自写软件\PDF编辑逆向软件\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\轻PDF编辑器"; Filename: "{app}\轻PDF编辑器.exe"; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"
Name: "{autodesktop}\轻PDF编辑器"; Filename: "{app}\轻PDF编辑器.exe"; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\轻PDF编辑器.exe"; Description: "启动 轻PDF编辑器"; Flags: nowait postinstall skipifsilent
