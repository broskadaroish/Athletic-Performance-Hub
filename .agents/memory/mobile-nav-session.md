---
name: Mobile nav session race condition
description: Warum mobile Bottom-Navigation die Session verlor und wie es gefixt wurde
---

## Problem
`<a href="?nav=xxx">` in der Bottom-Navigation erzeugt einen vollständigen Browser-Reload:
- Neue WebSocket-Verbindung zu Streamlit → `st.session_state` leer
- `CookieController.get("ath_sid")` gibt auf dem **ersten Run** `None` zurück (React-Komponente noch nicht initialisiert)
- Sofort: Login-Gate fällt durch → Login-Formular → `st.stop()`
- Desktop funktioniert, weil `st.radio` keinen Reload verursacht (gleiche WebSocket-Session)

## Fix (app.py, Login-Gate-Block)
Vor dem Login-Formular: wenn `_stored_sid` is None UND `_cookie_ctrl` vorhanden UND `_cookie_load_done` NICHT in session_state:
- `st.session_state["_cookie_load_done"] = True` setzen
- Lade-Platzhalter ("Sitzung wird geprüft …") anzeigen
- `st.stop()`

CookieController triggert dann automatisch Run 2 (React sendet Wert via setComponentValue).
Im Run 2 ist der echte Cookie-Wert verfügbar → Session wiederhergestellt → kein erneuter Login nötig.

## Warum _cookie_load_done funktioniert
`st.session_state` wird zwischen Streamlit-Reruns derselben WebSocket-Session bewahrt.
Nach einer neuen Browser-Navigation (neue WebSocket-Session) ist das Flag nicht gesetzt → Loading zeigen.
Auf dem zweiten Rerun (gleiche Session) ist das Flag gesetzt → Cookie-Prüfung auswerten.

**Why:** CookieController = React-Komponente → braucht immer 1 Rerun zur Initialisierung. Dieser Wartemechanismus ist für JEDEN CookieController-Einsatz in Streamlit nötig, wenn auf dem ersten Run eine Entscheidung abhängt.
