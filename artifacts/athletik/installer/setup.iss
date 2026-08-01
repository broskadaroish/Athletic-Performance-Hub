; ══════════════════════════════════════════════════════════════════════════════
; Bruce Football Performance Diagnostics — Inno Setup Script
; ══════════════════════════════════════════════════════════════════════════════

#define MyAppName      "Bruce Football Performance Diagnostics"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "Broska Daroish"
#define MyAppURL       "mailto:Broska_daroish@hotmail.de"
#define MyAppExeName   "BruceFootball.exe"
#define MyAppID        "{A3F2B8C1-4D9E-4A7F-B2C3-D5E6F7A8B9C0}"

; Build-Verzeichnis wird per /DMyBuildDir=... übergeben
#ifndef MyBuildDir
  #define MyBuildDir ".\\_build"
#endif
#ifndef MyOutputDir
  #define MyOutputDir ".\\Output"
#endif

[Setup]
AppId={{#MyAppID}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\BruceFootballDiagnostics
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#MyOutputDir}
OutputBaseFilename=BruceFootball_Setup_v{#MyAppVersion}
SetupIconFile={#MyBuildDir}\app\assets\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSmallImageFile={#MyBuildDir}\app\assets\app_logo.png
DisableWelcomePage=no
DisableDirPage=no
DisableReadyPage=no
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
ShowLanguageDialog=no
LanguageDetectionMethod=none
CloseApplications=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
german.AppIsRunning=Die Anwendung läuft noch. Bitte schließen Sie sie zuerst.
german.InstallingPython=Installiere Python-Umgebung...
german.AppDescription=Athletik-Diagnostik-Software für den Fußball

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Beim Windows-Start automatisch öffnen"; GroupDescription: "Autostart:"; Flags: unchecked

[Files]
; Python embedded
Source: "{#MyBuildDir}\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__"

; App-Dateien
Source: "{#MyBuildDir}\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc,backup_*"

; Launcher
Source: "{#MyBuildDir}\launcher.vbs";       DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildDir}\launcher.bat";       DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildDir}\stop.vbs";           DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Streamlit config
Source: "{#MyBuildDir}\streamlit_config\config.toml"; DestDir: "{app}\streamlit_config"; Flags: ignoreversion

; Launcher-EXE (kleines Wrapper-Script als .exe)  — wird als launcher.vbs gestartet
; Hinweis: Da kein PyInstaller verwendet wird, erzeugen wir einen .bat-Wrapper
; der als "Icon-Datei" mit dem richtigen Icon in der Taskleiste erscheint.

[Icons]
; Startmenü
Name: "{group}\{#MyAppName}";           Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\app\assets\app_icon.ico"; Comment: "Athletik-Diagnostik für Fußball"
Name: "{group}\{#MyAppName} beenden";   Filename: "{sys}\wscript.exe"; Parameters: """{app}\stop.vbs""";    WorkingDir: "{app}"; Comment: "Anwendung beenden"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\app\assets\app_icon.ico"; Tasks: desktopicon

; Autostart
Name: "{autostartup}\{#MyAppName}"; Filename: "{sys}\wscript.exe"; Parameters: """{app}\launcher.vbs"""; WorkingDir: "{app}"; Tasks: startupicon

[Registry]
; Daten-Verzeichnis beim ersten Start anlegen (via Installer vorregistrieren)
Root: HKCU; Subkey: "Software\BruceFootballDiagnostics"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\BruceFootballDiagnostics"; ValueType: string; ValueName: "DataPath";    ValueData: "{userappdata}\BruceFootballDiagnostics"; Flags: uninsdeletekey

[Dirs]
; Daten-Verzeichnis anlegen
Name: "{userappdata}\BruceFootballDiagnostics"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir: String;
  ConfigFile: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Streamlit config in den richtigen Pfad kopieren
    ConfigDir := ExpandConstant('{userappdata}\.streamlit');
    if not DirExists(ConfigDir) then
      CreateDir(ConfigDir);

    ConfigFile := ExpandConstant('{app}\streamlit_config\config.toml');
    if FileExists(ConfigFile) then
      FileCopy(ConfigFile, ConfigDir + '\config.toml', False);
  end;
end;

[UninstallRun]
; Laufende Instanz beenden
Filename: "{sys}\taskkill.exe"; Parameters: "/f /im python.exe"; Flags: runhidden; RunOnceId: "KillPython"

[UninstallDelete]
; Cache und Logs entfernen
Type: filesandordirs; Name: "{userappdata}\BruceFootballDiagnostics\__pycache__"
Type: filesandordirs; Name: "{app}\_build"
