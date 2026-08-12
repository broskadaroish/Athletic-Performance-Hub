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

## CookieController-Timing-Fix bleibt
`_cookie_load_done` Flag im Login-Gate bleibt für echte Browser-Reloads (Seite aktualisieren)
erhalten. Normale Nav-Klicks brauchen es nicht mehr.

**Why:** Internal Streamlit reruns (via setComponentValue) bewahren die gesamte
st.session_state. Nur echte Browser-Navigationen (neue WebSocket-Session) brauchen
den Cookie-Restore.

**How to apply:** Jede mobile Navigationsaktion muss über den Custom Component oder
über direkte st.session_state-Manipulation + st.rerun() laufen. KEIN `<a href>` für Navigation.
