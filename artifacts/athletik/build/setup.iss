; Inno Setup Script — Bruce Football Performance Diagnostics
; Compiler: Inno Setup 6 (https://jrsoftware.org/isinfo.php)
; Ausführen: ISCC.exe build\setup.iss

#define AppName "Bruce Football Performance Diagnostics"
#define AppVersion "1.0.0"
#define AppPublisher "Broska Daroish"
#define AppURL "mailto:Broska_daroish@hotmail.de"
#define AppExeName "BruceFootballPerformanceDiagnostics.exe"
#define AppCopyright "Copyright (c) 2026 Broska Daroish. Alle Rechte vorbehalten."

[Setup]
AppId={{F4A2B3C1-8D5E-4F6A-9B0C-1D2E3F4A5B6C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppCopyright={#AppCopyright}
DefaultDirName={autopf}\Bruce Football Performance Diagnostics
DefaultGroupName={#AppName}
AllowNoIcons=no
; Icon — muss als assets\icon.ico vorliegen
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
OutputDir=Output
OutputBaseFilename=BruceFootballPerformanceDiagnostics_Setup_v1.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon";    Description: "Desktop-Verknüpfung erstellen";    GroupDescription: "Verknüpfungen:"; Flags: checked
Name: "quicklaunchicon"; Description: "Schnellstart-Verknüpfung erstellen"; GroupDescription: "Verknüpfungen:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Alle Dateien aus dem PyInstaller-dist-Ordner
Source: "..\dist\BruceFootball\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";            Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Benutzerdaten in AppData werden NICHT gelöscht (Spieler-/Testdaten bleiben erhalten)
Type: filesandordirs; Name: "{app}"

[Code]
// Zeigt Lizenzhinweis beim Setup
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Diese Software installiert ' + '{#AppName}' + ' auf Ihrem Computer.' + #13#10 +
    '' + #13#10 +
    '{#AppCopyright}' + #13#10 +
    'Das Kopieren oder Verbreiten ohne Genehmigung ist untersagt.';
end;
