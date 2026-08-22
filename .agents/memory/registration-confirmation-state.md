---
name: Registration confirmation state
description: Scope and security boundary for the post-registration confirmation view.
---

The post-registration confirmation view stores only the pending account ID, displayed email address, and initial mail-send status in Streamlit session state. It survives Streamlit reruns but not a full browser reload.

**Why:** The confirmation view is temporary guidance, not authentication. Persisting it beyond the Streamlit session would require browser- or server-side state that could expose account information or add unnecessary token handling. Passwords and verification tokens must never enter session state.

**How to apply:** Keep registration success UI session-scoped. Reuse the database-backed verification-token and cooldown functions for resend actions. Do not add an automatic login or change activation when verifying an email; activation remains a separate administrator action.