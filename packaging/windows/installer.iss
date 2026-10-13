#ifndef AppVersion
  #error Pass /DAppVersion with the application VERSION value.
#endif
[Setup]
AppId={{97B412B1-0916-4D2C-91D0-385F173F699A}
AppName=AutoTyper Pro
AppVersion={#AppVersion}
AppPublisher=hamitcf1
AppPublisherURL=https://github.com/hamitcf1/AutoTyperPro
DefaultDirName={localappdata}\Programs\AutoTyperPro
DefaultGroupName=AutoTyper Pro
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installers
OutputBaseFilename=AutoTyperPro-{#AppVersion}-windows-x64-setup
SetupIconFile=..\..\assets\icon.ico
UninstallDisplayIcon={app}\AutoTyperPro.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts"; Flags: unchecked

[Files]
Source: "..\..\dist\AutoTyperPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AutoTyper Pro"; Filename: "{app}\AutoTyperPro.exe"
Name: "{autodesktop}\AutoTyper Pro"; Filename: "{app}\AutoTyperPro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AutoTyperPro.exe"; Description: "Launch AutoTyper Pro"; Flags: nowait postinstall skipifsilent
