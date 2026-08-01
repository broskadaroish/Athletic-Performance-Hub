' ══════════════════════════════════════════════════════════════
' Bruce Football Performance Diagnostics — Stopper
' ══════════════════════════════════════════════════════════════
Dim oShell
Set oShell = CreateObject("WScript.Shell")

' Streamlit-Prozesse beenden
oShell.Run "taskkill /f /fi ""WINDOWTITLE eq streamlit*"" /im python.exe", 0, True
oShell.Run "taskkill /f /fi ""IMAGENAME eq python.exe"" /fi ""CommandLine eq *streamlit*""", 0, True

MsgBox "Bruce Football Diagnostics wurde beendet.", vbInformation, "Bruce Football"
Set oShell = Nothing
