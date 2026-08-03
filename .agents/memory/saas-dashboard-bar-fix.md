---
name: saas_dashboard bar chart colorscale fix
description: Plotly Bar charts crash with 8-char hex alpha colors in colorscale
---

## Rule
Do not use `colorscale=[[0, color+"55"], [1, color]]` on `go.Bar` markers. Plotly's Bar.marker.colorscale does not accept 8-char hex colors with alpha.

## Bad
```python
marker=dict(colorscale=[[0, "#58a6ff55"], [1, "#58a6ff"]])  # ValueError
```

## Good
```python
marker=dict(color="#58a6ff")  # solid color, no gradient
```

**Why:** Plotly Bar colorscale only accepts proper colorscale formats. The `+="55"` alpha-hex hack only works in CSS, not in Plotly color specs.
