; Inno Setup Script — Bruce Football Performance Diagnostics
; Erstellt mit Inno Setup 6 (https://jrsoftware.org/isinfo.php)

#define AppName "Bruce Football Performance Diagnostics"
#define AppVersion "1.0.0"
#define AppPublisher "Bruce Football"
#define AppExeName "BruceFootballDiagnostics.exe"
#define AppDataDir "{userappdata}\BruceFootballDiagnostics"

[Setup]
AppId={{A3F2C1D0-7B4E-4F9A-8C3D-E1B2F5A6C7D8}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Bruce Football Performance Diagnostics
DefaultGroupName={#AppName}
AllowNoIcons=no
; Installer-Icon
SetupIconFile=..\assets\icon.ico
; Komprimierung
Compression=lzma2/ultra64
SolidCompression=yes
; UAC: Admin-Rechte für Installation in Programme-Ordner
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; Ausgabe
OutputDir=dist
OutputBaseFilename=BruceFootball_Setup_v{#AppVersion}
; Mindest-Windows-Version: Windows 10
MinVersion=10.0.17763
; Modernes Design
WizardStyle=modern
WizardSizePercent=110
; Lizenzdatei (optional — auskommentieren falls nicht vorhanden)
; LicenseFile=..\LICENSE.txt

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon";    Description: "Desktop-Verknüpfung erstellen";   GroupDescription: "Zusätzliche Symbole:"; Flags: checked
Name: "startmenuicon";  Description: "Startmenü-Eintrag erstellen";     GroupDescription: "Zusätzliche Symbole:"; Flags: checked
Name: "launchapp";      Description: "Anwendung nach Installation starten"; GroupDescription: ""; Flags: checked

[Dirs]
; Benutzerdaten-Ordner anlegen — bleiben bei Deinstallation erhalten
Name: "{userappdata}\BruceFootballDiagnostics";                      Flags: uninsneveruninstall
Name: "{userappdata}\BruceFootballDiagnostics\Berichte";             Flags: uninsneveruninstall
Name: "{userappdata}\BruceFootballDiagnostics\Trainingspläne";       Flags: uninsneveruninstall
Name: "{userappdata}\BruceFootballDiagnostics\Backups";              Flags: uninsneveruninstall
Name: "{userappdata}\BruceFootballDiagnostics\Logs";                 Flags: uninsneveruninstall

[Files]
; Gesamter PyInstaller-Build-Ordner
Source: "..\dist\BruceFootballDiagnostics\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Desktop
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon
; Startmenü
Name: "{group}\{#AppName}";         Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: startmenuicon
Name: "{group}\Deinstallieren";     Filename: "{uninstallexe}"

[Run]
; Nach Installation starten (optional)
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; Tasks: launchapp

[UninstallRun]
; App vor Deinstallation sauber beenden (falls noch offen)
Filename: "taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[UninstallDelete]
; Nur Programmdateien löschen — Benutzerdaten in APPDATA bleiben erhalten
Type: filesandordirs; Name: "{app}"

[Code]
// Prüfe ob eine alte Version läuft und beende sie vor dem Update
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    // Sicherstellen dass die App nicht läuft während der Installation
    Exec('taskkill.exe', '/F /IM BruceFootballDiagnostics.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
