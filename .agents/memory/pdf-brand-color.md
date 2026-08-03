---
name: PDF dynamic brand color + trainer name
description: How generate_report accepts club primary color and trainer name for PDF personalization
---

## Rule
`generate_report()` accepts `farbe_primaer: str | None` (hex like `#1e5a9c`) and `trainer_name: str`. These are applied at PDF creation time.

## How it works
```python
pdf = AthletikReport()
if farbe_primaer:
    h = farbe_primaer.lstrip("#")
    pdf.BRAND = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
```

The `BRAND` attribute is set on the instance (not the class), so it overrides the default `(20, 90, 160)` only for that PDF.

## Call site (app.py)
```python
_verein_pdf = verein_by_id(_akt_user().get("verein_id") or 0) or {}
pdf_bytes = generate_report(
    ...
    trainer_name=st.session_state.get("cfg_trainer_name", ""),
    farbe_primaer=_verein_pdf.get("farbe_primaer"),
)
```

## Trainer name display
- Shown in the cover page header (bottom-left of the blue band)
- Uses `_safe()` encoding

**Why:** PDFs should reflect club branding and show the responsible trainer for professional parent meetings and medical handoffs.
