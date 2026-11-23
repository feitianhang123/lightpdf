[Setup]
AppId={{B2F5D0E1-7A3C-4E9B-9C21-8F4A6D2E1B33}
AppName=轻PDF编辑器
AppVersion=1.0.17
AppVerName=轻PDF编辑器 1.0.17
AppPublisher=轻PDF编辑器
DefaultDirName={autopf}\轻PDF编辑器
DefaultGroupName=轻PDF编辑器
DisableProgramGroupPage=yes
OutputDir=安装包
OutputBaseFilename=setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\轻PDF编辑器.exe
UninstallDisplayName=轻PDF编辑器
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

; ---------------------------------------------------------------------------
; 数字签名（可选，默认关闭）：购买 Authenticode 代码签名证书后，取消下面两行
; 注释，即可让 Inno Setup 自动签名 setup.exe 与 unins000.exe，安装界面上的
; 「未知发布者」会变成已验证的发布者名称。
;   1) 主程序 dist\轻PDF编辑器.exe 需要在运行 ISCC 之前先单独签一次：
;      signtool sign /a /fd SHA256 /tr http://timestamp.sectigo.com /td SHA256 /d "轻PDF编辑器" "dist\轻PDF编辑器.exe"
;   2) SignTool 里的 $f 会被替换成待签文件；时间戳 URL 按证书颁发机构选择：
;      Sectigo    http://timestamp.sectigo.com
;      DigiCert   http://timestamp.digicert.com
;      Certum     http://time.certum.pl
;      GlobalSign http://timestamp.globalsign.com
;   3) /a 自动挑选本机证书库里的证书；若有多张，改用 /sha1 <证书指纹>。
;   4) 时间戳（/tr + /td）务必保留：证书过期后已发布的安装包仍能验证有效。
;   5) 签名会改变文件哈希，重新发布后需同步更新 README 与 Release 的 SHA-256。
; ---------------------------------------------------------------------------
; SignTool="signtool" sign /a /fd SHA256 /tr http://timestamp.sectigo.com /td SHA256 /d "轻PDF编辑器" $f
; SignedUninstaller=yes

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "dist\轻PDF编辑器.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\轻PDF编辑器"; Filename: "{app}\轻PDF编辑器.exe"; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"
Name: "{autodesktop}\轻PDF编辑器"; Filename: "{app}\轻PDF编辑器.exe"; IconFilename: "{app}\icon.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\轻PDF编辑器.exe"; Description: "启动 轻PDF编辑器"; Flags: nowait postinstall skipifsilent
