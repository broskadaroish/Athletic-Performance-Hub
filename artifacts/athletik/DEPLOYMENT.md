# Athletik App — Deployment & Production-Readiness Report

Stand: 2026-08-03

---

## ✅ Umgesetzte Verbesserungen

### Sicherheit

| # | Problem | Fix |
|---|---|---|
| 1 | **Passwort-Hashing: SHA-256 ohne Salt** (Rainbow-Table-Angriff möglich) | PBKDF2-SHA256 mit zufälligem 128-Bit-Salt (260.000 Iterationen) — `database.py: _pw_hash()` |
| 2 | **Kein Timing-sicherer Vergleich** | `hmac.compare_digest()` verhindert Timing-Angriffe bei Hash-Vergleich — `database.py: _pw_verify()` |
| 3 | **Automatische Hash-Migration** | Beim ersten erfolgreichen Login mit altem SHA-256-Hash wird der Hash transparent auf PBKDF2 upgegradet — `auth.py` |

### Datenbank

| # | Änderung | Datei |
|---|---|---|
| 1 | **WAL-Modus aktiviert** (`PRAGMA journal_mode=WAL`) — bessere Concurrent-Read-Performance, kein Write-Lock für Reads | `database.py: get_conn()` |
| 2 | **`PRAGMA synchronous=NORMAL`** — mit WAL: sicher und deutlich schneller als FULL | `database.py: get_conn()` |
| 3 | **32 MB Query-Cache** (`PRAGMA cache_size=-32000`) | `database.py: get_conn()` |
| 4 | **Temp-Tabellen im RAM** (`PRAGMA temp_store=MEMORY`) | `database.py: get_conn()` |
| 5 | **Connection-Timeout 30 s** — verhindert sofortigen Absturz bei kurzzeitiger DB-Last | `database.py: get_conn()` |
| 6 | **Rollback bei Fehler** — Exception in DB-Operationen rollt jetzt zurück statt silent fail | `database.py: get_conn()` |
| 7 | **DB-Pfad per Umgebungsvariable** (`ATHLETIK_DB_PATH`) — kein Hardcode mehr | `database.py` |
| 8 | **Performance-Indizes** auf `spieler_id`, `verein_id`, `datum` für alle 10 Test-Tabellen | `database.py: _create_indexes()` |

### Performance

| # | Änderung | Datei |
|---|---|---|
| 1 | **Cache-TTL 300 s** für PDF-Generierung — verhindert unbegrenzte Speicher-Akkumulation | `app.py` |
| 2 | **`PRAGMA cache_size`** — häufig gelesene Seiten bleiben im RAM | `database.py` |
| 3 | **WAL-Modus** — parallele Reads ohne Blockierung durch aktive Writes | `database.py` |

### Konfiguration

| # | Änderung | Datei |
|---|---|---|
| 1 | **`maxUploadSize = 10 MB`** explizit gesetzt | `.streamlit/config.toml` |
| 2 | **`fastReruns = true`** aktiviert | `.streamlit/config.toml` |
| 3 | **Secrets-Vorlage erstellt** | `.streamlit/secrets.toml.example` |

---

## ⚠️ Offene Punkte für Livebetrieb

### Kritisch (vor Go-Live klären)

| # | Punkt | Empfehlung |
|---|---|---|
| 1 | **SQLite in Multi-User-Produktion** | SQLite ist für ≤ 10 gleichzeitige Schreibvorgänge geeignet. Bei mehr Vereinen gleichzeitig → Migration auf PostgreSQL (Struktur ist vorbereitet: alle Queries parametrisiert, DB-Pfad konfigurierbar) |
| 2 | **Persistenter Datenbankpfad** | In Cloud-Deployments (Replit, Heroku, Railway) ist das Dateisystem ephemeral. DB-Datei muss auf ein gemountetes Volume gelegt werden: `ATHLETIK_DB_PATH=/data/athletik.db` |
| 3 | **Backup-Strategie** | Aktuell: keine automatischen Backups. Empfehlung: täglicher `sqlite3 athletik.db ".backup /backup/athletik_$(date +%Y%m%d).db"` per Cron |
| 4 | **HTTPS erzwingen** | App selbst macht kein TLS. Reverse-Proxy (nginx, Caddy) oder Cloud-Dienst muss HTTPS terminieren |
| 5 | **XSRF-Schutz** | `enableXsrfProtection = false` ist für Proxy-Betrieb nötig. Bei direktem HTTPS-Betrieb ohne Proxy: auf `true` setzen |

### Mittel

| # | Punkt | Empfehlung |
|---|---|---|
| 6 | **Datei-Upload Magic-Byte-Prüfung** | `st.file_uploader(type=[...])` prüft nur die Dateiendung (Client-seitig). Server-seitige MIME-Prüfung anhand Magic Bytes fehlt noch |
| 7 | **Rate-Limiting für Login** | Kein Brute-Force-Schutz. Nach N Fehlversuchen temporäre Sperre empfohlen |
| 8 | **Session-Invalidierung** | Gestohlener Session-State (Streamlit: `st.session_state`) ist nach Passwortänderung weiterhin gültig — Task #114 in der Aufgabenliste |
| 9 | **Backup-Dateien im Projektordner** | `athletik_BACKUP_*.db` und `backup_20260729_*.py` im Arbeitsverzeichnis — nicht in Produktion deployen (`.gitignore` empfohlen) |
| 10 | **Log-Rotation** | Streamlit schreibt in stdout. Für Produktion: Log-Aggregation (z. B. Loki, Papertrail) empfohlen |

### Niedrig

| # | Punkt | Empfehlung |
|---|---|---|
| 11 | **`use_container_width` deprecated** | Streamlit warnt: ab 2025-12-31 wird `use_container_width` durch `width='stretch'` ersetzt. Viele Stellen in `app.py` |
| 12 | **Leeres Label bei Navigation** | Pre-existing Streamlit-Warnung bei Nav-Radio-Widget (kein echter Bug) |

---

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `ATHLETIK_DB_PATH` | `athletik.db` | Absoluter oder relativer Pfad zur SQLite-Datenbank |
| `PORT` | `8082` | Port (wird von Replit automatisch gesetzt) |

---

## Deployment-Checkliste

- [ ] `ATHLETIK_DB_PATH` auf persistenten Speicher setzen
- [ ] Backup-Skript einrichten (täglich)
- [ ] HTTPS über Reverse-Proxy oder Cloud-Dienst sicherstellen
- [ ] Backup-Dateien (`.db`, `backup_*.py`) aus Produktionsimage ausschließen
- [ ] `secrets.toml` aus `secrets.toml.example` erstellen (nicht in Git einchecken)
- [ ] Erster Superadmin-Login: Passwort sofort nach Ersteinrichtung ändern (wird dann auf PBKDF2 upgegradet)

---

## Nicht geändert (explizit ausgeschlossen)

- Keine fachlichen Änderungen an Diagnostik, Normwerten oder Algorithmen
- Keine PostgreSQL-Umstellung (Struktur vorbereitet, aber noch SQLite)
