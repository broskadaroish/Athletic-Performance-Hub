---
name: Mobile nav final architecture
description: How the bottom nav works — hidden st.button triggers clicked by inline JS onclick. Replaces failed declare_component and <a href> approaches.
---

## Rule
The mobile bottom nav uses `<button onclick>` elements in a visually rendered `<nav class="aph-bottom-nav">`. Each onclick finds a hidden `st.button` labelled `⬡IDX` (U+2B21 White Hexagon) by `textContent` and calls `.click()` programmatically. This triggers Streamlit's WebSocket rerun — same session, no cookie restore needed.

**Why:** Two previous approaches failed:
1. `<a href="?nav=xxx">` caused full page reload → new WebSocket session → st.session_state lost → cookie re-read race condition.
2. `st.components.v1.declare_component(path=...)` times out in Replit's mTLS proxy because `/_stcore/component/` cannot be served from local file paths through the proxy.

**How to apply:**
- All nav targets are in `_ALL_TARGETS` list in `mobile.py`, indexed 0–N.
- `render_mobile_nav()` renders the visual `<nav>` AND `st.columns(N)` of hidden trigger buttons at the END of the page.
- MutationObserver (started by `<img onerror>`) hides trigger columns off-screen via `position:absolute;top:-9999px`.
- When JS clicks a hidden button: Streamlit receives widget event → `_apply_nav_signal(target)` runs → `st.session_state` updated → `st.rerun()`.
- `<a href>` / `st.page_link` / `declare_component` must never be used for this nav.

## Chrome auto-translate fix (the "sündigen" bug)
Chrome Mobile auto-translates pages without `lang="de"` on the `<html>` element. The `<img src="x" onerror="...">` (rendered every rerun by `st.markdown`) sets:
```javascript
document.documentElement.lang = 'de';
document.documentElement.setAttribute('translate', 'no');
```
All nav HTML also carries `translate="no"` attribute as belt-and-suspenders.

**Why onerror:** `<script>` blocks in `st.markdown` do NOT execute (React strips them for security). Only event handler attributes (`onclick`, `onerror`) and `<style>` blocks work in `unsafe_allow_html`.

## Key files
- `mobile.py` — `_ALL_TARGETS`, `_TARGET_TO_IDX`, `_bn_onclick()`, `_apply_nav_signal()`, `render_mobile_nav()`, `inject_mobile_mehr_overlay()`
- `theme.py` — `.aph-bottom-nav` (position:fixed) + `.aph-bn-item` (button reset styles) + `.aph-mehr-item`/`.aph-mehr-close`/`.aph-mph-switch` (all `<button>` reset styles)
- `app.py` — calls `render_mobile_nav(section)` at end of page (line ~10005)

## CSS button reset pattern
Any interactive element that was `<a href>` must become `<button type="button">` with CSS:
```css
background: none; border: none; cursor: pointer; font-family: inherit;
-webkit-tap-highlight-color: transparent;
```
