---
name: Mixed-type DataFrame Arrow serialization bug
description: st.dataframe crashes with ArrowInvalid when numeric columns contain "—" strings
---

## Rule
Never mix numeric values and `"—"` strings in the same DataFrame column when passing to `st.dataframe`. Use `None` for missing numeric values instead.

## Bad
```python
"FMS": fms["score"] if fms else "—"  # mixed int/str → ArrowInvalid
```

## Good
```python
"FMS": int(fms["score"]) if fms else None  # nullable int → OK
```

**Why:** PyArrow (used by Streamlit's st.dataframe) cannot serialize columns with mixed types. The error is `ArrowInvalid: Could not convert '—' with type str: tried to convert to int64`.

**Where fixed:** Kader-Export in page_einstellungen (Mannschaft-Tab), ~line 6230 of app.py.
