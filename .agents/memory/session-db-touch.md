---
name: Session DB-Touch
description: "session_validieren() aktualisiert letzte_aktivitaet nur im Login-Gate. Aktive WS-Sessions brauchen throttled DB-Touch alle 5 Minuten, sonst idle-Timeout trotz Aktivität."
---

## Die Regel
`session_validieren()` — die einzige Funktion, die `letzte_aktivitaet` in der DB aktualisiert — wird **nur im Login-Gate** aufgerufen (wenn `"user" not in st.session_state`).

Der per-Rerun-Check `session_token_aktiv()` prüft nur `s.aktiv` und `token_version`, aktualisiert `letzte_aktivitaet` aber **nicht**.

## Folge ohne Fix
Ein Nutzer, der > `idle_sek` (Standard: 3600s = 60min) aktiv arbeitet, ohne den Browser zu laden (WebSocket bleibt am Leben), hat nach dieser Zeit eine DB-Session mit abgelaufener `letzte_aktivitaet`. Beim nächsten Reconnect (Display-Lock, App-Wechsel, Netzunterbrechung) ruft der Login-Gate `session_validieren()` auf → findet idle-expired → gibt None zurück → zeigt Login-Formular, obwohl der Nutzer aktiv war.

## Fix (implementiert)
1. `database.py`: `session_aktivitaet_aktualisieren(token)` — fail-open UPDATE `letzte_aktivitaet WHERE token=? AND aktiv=1`
2. `app.py`: Throttled DB-Touch alle 5 Minuten nach dem `session_token_aktiv()` Check. Tracking via `st.session_state["_last_db_touch_ts"]`.

## Why
Dual-Timeout-Architektur: `session_timeout.py` nutzt client-seitigen `_last_active` im session_state (korrekt für WebSocket-Verlust), aber DB `letzte_aktivitaet` veraltete ohne regelmäßiges Update.

## How to apply
- Nie `session_validieren()` für den per-Rerun-Security-Check verwenden (zu teuer, schreibt viel)
- `session_token_aktiv()` für den schnellen per-Rerun-Check behalten
- `session_aktivitaet_aktualisieren()` immer throttled aufrufen (min. 5 Minuten Abstand)
- `_COOKIE_MAX_WAIT` = 8 (war 4) bei langsamen mobilen Verbindungen ausreichend
