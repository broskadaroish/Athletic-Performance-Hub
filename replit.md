# Football Athletik Diagnostik System

A professional football athletic performance platform for elite academy use — covering player management, movement assessments (FMS + Y-Balance), automatic injury risk scoring, training plan generation, 12-week periodization, progress tracking, and PDF reports.

## Run & Operate

- **Start app:** workflow `Football Atletik App` — `cd athletik && streamlit run app.py --server.port 5000`
- The Streamlit UI is served at port **5000**
- Database file: `athletik/athletik.db` (SQLite, auto-created on first run)

## Stack

- Python 3 + Streamlit 1.6
- Plotly for charts, Pandas for data frames, fpdf2 for PDF reports
- SQLite (via stdlib `sqlite3`) — no ORM

## Where things live

```
athletik/
├── app.py              # Main entry point — all pages + navigation + CSS
├── database.py         # DB layer — context-manager connections, all SQL
├── fms.py              # FMS dataclass — scoring, asymmetry, risk, schwerpunkt
├── y_balance.py        # Y-Balance dataclass — composite scores, asymmetry detection
├── training.py         # Exercise library + area-based lookup + schwerpunkt parser
├── periodisierung.py   # 12-week periodization engine (3 phases)
├── analytics.py        # Risk score, athletik score, deficit detection
├── pdf_report.py       # fpdf2 PDF report generator
└── .streamlit/
    └── config.toml     # Server config (port 5000, headless)
```

## Architecture decisions

- **Single `app.py` with page functions** — avoids Streamlit multi-page import complexity; each page is a plain Python function called from the sidebar router.
- **`sqlite3.Row` factory** — all DB rows behave like dicts; eliminates magic integer column indexing from the original codebase.
- **Context-manager DB connections** — `with get_conn() as conn` guarantees commit+close even on exceptions; no leaked connections.
- **Dataclasses for FMS + Y-Balance** — computed properties (score, asymmetry, risk level) live on the model, not scattered across UI code.
- **`analytics.py` as dedicated engine** — risk scoring, athletik score, and deficit detection are pure functions; easy to unit-test and reuse.

## Product

- **Coach Dashboard** — team-wide risk breakdown, per-player athletik scores, interactive bar + pie charts
- **Player Management** — create/view/delete players with position, dominant leg, team
- **Player Profile** — single-player view with risk badge, score badge, deficit cards, training recommendations, PDF download
- **FMS Test** — 7-pattern bilateral input, automatic composite score, pattern progress bars
- **Y-Balance Test** — composite score calculation, radar chart, bilateral comparison
- **Training Plan** — auto-generated from diagnostics or manually constructed, organised by week
- **Periodization** — auto 12-week plan split into Stabilisation / Kraft / Fußball phases
- **Progress Tracking** — FMS + Y-Balance history charts with threshold lines

## User preferences

- Immer auf Deutsch antworten.

## Gotchas

- `training_standard_laden()` / `init_training_bibliothek()` is idempotent — safe to call on every startup; it checks `COUNT(*)` before inserting.
- `training.py` has `list[str]` type hints requiring Python 3.9+. The environment ships Python 3.11.
- PDF reports use fpdf2 (not fpdf). The package name is `fpdf2` but imports as `from fpdf import FPDF`.
