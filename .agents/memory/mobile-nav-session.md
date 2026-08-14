---
name: Mobile nav session race condition — endgültige Lösung
description: Warum die Bottom-Navigation die Session verlor und wie es ENDGÜLTIG behoben wurde
---

## Problem
`<a href="?nav=xxx">` erzeugt eine vollständige Browser-Navigation:
- Neue WebSocket-Verbindung → st.session_state leer → Login-Gate → Session-Verlust
- Der CookieController-Timing-Fix (1 Extra-Rerun mit "_cookie_load_done") löste das
  Grundproblem NICHT, weil auf dem Smartphone der Cookie-Restore selbst flaky war.

## Endgültige Lösung: Streamlit Custom Component
Datei: `artifacts/athletik/components/mobile_nav/index.html`

Die Bottom-Navigation ist jetzt ein **deklarierter Custom Component** (`st.components.v1.declare_component`):
- Rendert 5 `<button>` Elemente (KEIN `<a href>`)
- Kommuniziert Klicks via `Streamlit.setComponentValue()` (raw postMessage-Protokoll)
- Positioniert sich selbst als `position:fixed` am Seitenende durch DOM-Zugriff auf
  `window.parent.document.querySelectorAll('iframe')` (same-origin, lokal serviert)
- Kein Browser-Reload — dieselbe WebSocket-Session bleibt erhalten

## Mehr-Overlay & Player-Header
Konvertiert von `<a href>` zu `<button onclick>` mit INLINE JavaScript:
```javascript
(function(t){
  var fs=window.parent.document.querySelectorAll('iframe');
  for(var i=0;i<fs.length;i++){try{fs[i].contentWindow.postMessage({aphNav:t},'*');}catch(e){}}
})('TARGET')
```
Der Component-iframe empfängt `{aphNav: target}` und leitet weiter an Streamlit.

## Wichtige Falle: <script> in st.markdown
`<script>` Tags in `st.markdown(unsafe_allow_html=True)` werden von React NICHT ausgeführt
(dangerouslySetInnerHTML Security). Nur Inline-Event-Handler (`onclick`, `onchange`, `onerror`)
funktionieren. Immer Inline-JS für Callbacks nutzen, nie externe Funktionen aufrufen.

## Deduplication der Nav-Signale
```python
if last.get("target") != target or last.get("ts") != ts:
    st.session_state["_mobile_nav_last"] = nav_signal
    _apply_nav_signal(target)
```
`ts: Date.now()` in jedem Signal verhindert Stale-Value-Loops über Reruns hinweg.

## CookieController-Timing-Fix: Multi-Retry (Phase A5.2)
`_cookie_load_done` (bool, 1 Rerun) wurde ersetzt durch `_cookie_load_attempts` (int, max 4 Reruns).

**Warum 4 statt 1:** Nach top-level Navigation von externen Seiten (Stripe Checkout, OAuth)
baut Streamlit eine neue WebSocket-Session auf. Die React-Komponente braucht dabei
oft 2–4 Zyklen bis der Cookie-Wert verfügbar ist. 1 Rerun reichte nicht.

**Cookie-Attribute für externe Redirects:**
- `same_site="Lax"` (nicht Strict) → Cookie wird bei GET-Redirects von Drittseiten gesendet
- `path="/"` → Cookie gilt für gesamte Domain, nicht nur aktuellen Streamlit-Pfad
- `secure=True` → nur HTTPS

**sessions-Tabelle:** kein `id`-Feld, nur `rowid` (SQLite intern). Cleanup-Query muss `rowid` nutzen.

**Soft-Cleanup:** session_erstellen() deaktiviert älteste Sessions wenn >5 aktive pro Benutzer.
Verhindert Ansammlung durch wiederholte Stripe-induzierte Neu-Logins.

**?checkout=success Preservation:** Query-Param bleibt in Browser-URL erhalten über alle
Reruns bis Session wiederhergestellt. Verarbeitung erst nach Login-Gate (Position ~70470 > ~13650).

**Why:** External navigation creates new Streamlit WebSocket → CookieController re-mounts
and needs multiple cycles. Counter approach is bounded (hard limit) and safe (no auth bypass).

**How to apply:** Jede externe Navigation (OAuth, Payment, etc.) braucht den multi-retry
Mechanismus. Kein Token in URL setzen.
