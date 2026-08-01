' ══════════════════════════════════════════════════════════════
' Bruce Football Performance Diagnostics — Launcher
' Startet den Streamlit-Server und öffnet den Browser.
' Läuft ohne sichtbares Konsolenfenster.
' ══════════════════════════════════════════════════════════════

Option Explicit

Dim oShell, oFSO, strBase, strData, strPython, strApp, strConfig
Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")

' ── Pfade ──────────────────────────────────────────────────────
strBase   = oFSO.GetParentFolderName(WScript.ScriptFullName)
strData   = oShell.ExpandEnvironmentStrings("%APPDATA%") & "\BruceFootballDiagnostics"
strPython = strBase & "\python\python.exe"
strApp    = strBase & "\app\app.py"
strConfig = strBase & "\streamlit_config"

' ── Daten-Verzeichnis anlegen ──────────────────────────────────
If Not oFSO.FolderExists(strData) Then
    oFSO.CreateFolder(strData)
End If

' ── Prüfen ob App schon läuft (Port 8501) ─────────────────────
Dim oHTTP
Set oHTTP = CreateObject("MSXML2.XMLHTTP")
On Error Resume Next
oHTTP.Open "GET", "http://localhost:8501", False
oHTTP.Send
Dim bAlreadyRunning
bAlreadyRunning = (Err.Number = 0 And oHTTP.Status = 200)
On Error GoTo 0

If bAlreadyRunning Then
    ' Nur Browser öffnen — Server läuft schon
    oShell.Run "http://localhost:8501", 1, False
    WScript.Quit
End If

' ── Streamlit starten (versteckt) ─────────────────────────────
Dim strCmd
strCmd = """" & strPython & """ -m streamlit run """ & strApp & """" & _
         " --server.headless=true" & _
         " --server.port=8501" & _
         " --server.address=localhost" & _
         " --browser.gatherUsageStats=false"

' Arbeitsverzeichnis = Daten-Ordner (dort liegt die athletik.db)
oShell.CurrentDirectory = strData
oShell.Run "cmd /c " & strCmd, 0, False

' ── Warten bis Server bereit (max. 30s) ───────────────────────
Dim i, bReady
bReady = False
For i = 1 To 30
    WScript.Sleep 1000
    On Error Resume Next
    oHTTP.Open "GET", "http://localhost:8501/_stcore/health", False
    oHTTP.Send
    If Err.Number = 0 And oHTTP.Status = 200 Then
        bReady = True
        Exit For
    End If
    On Error GoTo 0
Next

' ── Browser öffnen ─────────────────────────────────────────────
WScript.Sleep 500
oShell.Run "http://localhost:8501", 1, False

Set oShell = Nothing
Set oFSO   = Nothing
