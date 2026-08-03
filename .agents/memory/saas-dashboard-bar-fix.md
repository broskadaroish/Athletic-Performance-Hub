---
name: Plotly 8-char hex alpha color fix
description: Plotly crashes on any property that receives an 8-char hex color (e.g. #rrggbbaa)
---

## Rule
Never pass 8-char hex alpha strings (`color + "18"`, `color + "55"` etc.) to ANY Plotly color property. This fails for `fillcolor`, `colorscale`, and likely others.

## Bad
```python
fillcolor=color + "18"          # ValueError: Invalid value '#bc8cff18'
colorscale=[[0, color+"55"], [1, color]]  # ValueError on Bar marker
```

## Good — for solid colors
```python
marker=dict(color=color)
```

## Good — for transparent fill (Scatter fillcolor)
```python
fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.09)"
```

**Why:** Plotly only accepts 6-char hex, rgb(), rgba(), hsl(), hsla(), or CSS named colors. The CSS `#rrggbbaa` 8-char alpha notation is not supported anywhere in Plotly's color validators.

**Where fixed:** `saas_dashboard.py` — `_bar()` (marker colorscale) and `_line()` (scatter fillcolor).
