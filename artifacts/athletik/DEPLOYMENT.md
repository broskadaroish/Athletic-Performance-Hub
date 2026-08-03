# Athletik App — Production-Readiness Report

Stand: 2026-08-03

---

## Projektstruktur nach Produktions-Setup

```
artifacts/athletik/
│
├── app.py                    # Haupt-Einstiegspunkt (Streamlit)
├── config.py                 # ★ NEU — zentrale Env-Var-Konfiguration
├── logging_config.py         # ★ NEU — Logging (rotierend, Fehlerlog)
├── database.py               # SQLite-Datenbankschicht
│
├── utils/
│   └── file_magic.py         # ★ NEU — Magic-Byte-Validierung für Uploads
│
├── modules/                  # Feature-Module
│   ├── benutzerverwaltung.py
│   ├── trainerportal.py      # ★ geändert — Foto-Uploads abgesichert
│   ├── vereine.py
│   └── saas_dashboard.py
│
├── tools/
│   ├── create_superadmin.py
│   └── migrate_to_pg.py      # ★ NEU — SQLite → PostgreSQL Datenmigration
│
├── uploads/                  # ★ NEU — persistenter Datenspeicher
│   ├── logos/                #   Vereinslogos (Filesystem-Fallback)
│   ├── spielerbilder/        #   Spielerfotos (Filesystem-Fallback)
│   ├── pdf/                  #   generierte PDFs (für späteren Disk-Export)
│   ├── exports/              #   Excel-Exporte
│   ├── backups/              #   Datenbank-Backups
│   └── docs/                 #   eigene Protokolle / Anleitungen (früher assets/custom_docs/)
│
├── logs/                     # ★ NEU — Logdateien (nur in Produktion befüllt)
│   ├── athletik.log          #   rotierend, max 50 MB (10 × 5 MB)
│   └── error.log             #   nur ERROR+, max 25 MB (5 × 5 MB)
│
├── start.sh                  # ★ NEU — Startskript (Render / Railway / VPS / Docker)
├── Procfile                  # ★ NEU — für Render / Heroku
├── Dockerfile                # ★ NEU — Container-Image
├── docker-compose.yml        # ★ NEU — VPS Self-Hosting
├── render.yaml               # ★ NEU — Render.com Deployment-Konfiguration
├── railway.toml              # ★ NEU — Railway.app Deployment-Konfiguration
├── nginx.conf.example        # ★ NEU — nginx Reverse Proxy + SSL
├── .env.example              # ★ NEU — alle Env-Vars dokumentiert
├── .gitignore                # ★ NEU — vollständig (Secrets, DB, Uploads, Backups)
├── .dockerignore             # ★ NEU
├── requirements.txt          # ★ geändert — + psycopg2-binary, python-dotenv
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example  # ★ NEU
```

---

## ✅ Umgesetzte Maßnahmen

### 1. Zentrale Konfiguration (`config.py`)

Alle Umgebungsvariablen werden **ausschließlich** in `config.py` gelesen.
Kein anderes Modul greift mehr direkt auf `os.environ` zu.

| Env-Variable | Standard | Beschreibung |
|---|---|---|
| `APP_ENV` | `development` | `development` oder `production` |
| `PORT` | `8082` | Wird von Render/Railway automatisch gesetzt |
| `ATHLETIK_DATA_DIR` | App-Verzeichnis | Absoluter Pfad zu persistentem Volume |
| `ATHLETIK_DB_PATH` | `$DATA_DIR/athletik.db` | SQLite-Datenbankpfad |
| `DATABASE_URL` | *(nicht gesetzt)* | PostgreSQL-URL — wenn gesetzt, wird PG genutzt |
| `SESSION_SECRET` | *(Placeholder)* | **Muss** in Produktion gesetzt werden |
| `LOG_LEVEL` | `WARNING` (prod) | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `MAX_UPLOAD_MB` | `10` | Gesamt-Upload-Limit |
| `MAX_LOGO_MB` | `2` | Vereinslogo-Limit |
| `MAX_SPIELERBILD_MB` | `5` | Spielerfoto-Limit |
| `BEHIND_PROXY` | `1` | 1 = App läuft hinter Reverse Proxy |

### 2. Logging (`logging_config.py`)

| Feature | Entwicklung | Produktion |
|---|---|---|
| Konsolen-Ausgabe (stdout) | ✓ | ✓ |
| Rotierende Logdatei `logs/athletik.log` | — | ✓ (10 × 5 MB) |
| Fehler-Logdatei `logs/error.log` | — | ✓ (5 × 5 MB, nur ERROR+) |
| Bibliotheks-Logger gedrosselt | ✓ | ✓ |
| Format: `DATUM [LEVEL] modul: Nachricht` | ✓ | ✓ |

### 3. Dateiupload-Absicherung (`utils/file_magic.py`)

Magic-Byte-Prüfung (Server-seitig) für **alle** Uploads:

| Upload-Stelle | Geprüft | Erlaubte Formate |
|---|---|---|
| Vereinslogo (Einstellungen) | ✓ | JPEG, PNG, GIF, WebP |
| Vereinslogo (PDF-Export) | ✓ | JPEG, PNG, GIF, WebP |
| Trainerfoto (Admin-Verwaltung) | ✓ | JPEG, PNG, GIF, WebP |
| Profilfoto (Mein Profil) | ✓ | JPEG, PNG, GIF, WebP |
| Eigene Dokumente (Anleitungen, Protokolle) | ✓ | PDF |

### 4. Ordnerstruktur

`uploads/` und `logs/` werden beim App-Start **automatisch** angelegt:
- In Entwicklung: im App-Verzeichnis
- In Produktion: unter `ATHLETIK_DATA_DIR` (persistentes Volume)

Eigene Dokumente (früher: `assets/custom_docs/`) liegen jetzt in
`uploads/docs/` — damit auf dem persistenten Volume, nicht im Code-Image.

### 5. Deployment-Dateien

| Datei | Zweck |
|---|---|
| `start.sh` | Einheitliches Startskript für alle Hosting-Umgebungen |
| `Procfile` | Render / Heroku |
| `render.yaml` | Render.com (Web-Service + Volume + Env-Vars) |
| `railway.toml` | Railway.app |
| `Dockerfile` + `docker-compose.yml` | VPS Self-Hosting mit Docker |
| `nginx.conf.example` | Reverse Proxy + Let's Encrypt SSL |
| `.gitignore` | Secrets, DB-Dateien, Uploads, Backups ausgeschlossen |
| `.dockerignore` | Schlankes Docker-Image |

### 6. PostgreSQL-Vorbereitung

| Maßnahme | Status |
|---|---|
| `psycopg2-binary` in `requirements.txt` | ✓ |
| `DATABASE_URL`-Erkennung in `config.py` | ✓ |
| `postgres://` → `postgresql://` Normalisierung | ✓ |
| `tools/migrate_to_pg.py` — vollständiges Migrations-Skript | ✓ |
| SQLite bleibt Standard (keine PG-Pflicht) | ✓ |

### 7. Sicherheit (vorherige Session)

| Maßnahme | Status |
|---|---|
| PBKDF2-SHA256 Passwort-Hashing (260.000 Iterationen) | ✓ |
| Timing-sicherer Hash-Vergleich (`hmac.compare_digest`) | ✓ |
| Auto-Upgrade alter SHA-256-Hashes beim Login | ✓ |
| WAL-Modus + 14 DB-Performance-Indizes | ✓ |
| Rollback bei DB-Fehler | ✓ |

### 8. Aufgeräumt

- 11 Backup-Dateien aus dem Projektordner entfernt (`backup_*.py`, `athletik_BACKUP_*.db`)

---

## Deployment-Anleitungen

### Option A — Render.com (empfohlen für SaaS)

1. GitHub-Repository mit dem Render-Account verbinden
2. **New Web Service** → Repo auswählen → `render.yaml` wird automatisch erkannt
3. Im Dashboard Secrets setzen:
   - `SESSION_SECRET` → `python -c "import secrets; print(secrets.token_hex(32))"`
   - `SECRET_KEY` → wie oben
4. **Disk** `athletik-data` wird unter `/data` gemountet
5. Ersten Superadmin anlegen: `python tools/create_superadmin.py`

### Option B — Railway.app

1. GitHub-Repository verbinden → `railway.toml` wird erkannt
2. Env-Vars im Dashboard setzen (siehe `.env.example`)
3. Für persistenten Storage: Volume-Service hinzufügen, mounten unter `/mnt/data`

### Option C — VPS mit Docker

```bash
# 1. .env-Datei aus Vorlage erstellen
cp .env.example .env
# SESSION_SECRET und SECRET_KEY in .env eintragen

# 2. Starten
docker-compose up -d

# 3. nginx einrichten
sudo cp nginx.conf.example /etc/nginx/sites-available/athletik
sudo ln -s /etc/nginx/sites-available/athletik /etc/nginx/sites-enabled/
# Domain in nginx.conf anpassen, Zertifikat mit certbot holen
sudo certbot --nginx -d deinedomain.de
sudo systemctl reload nginx
```

### PostgreSQL-Migration (wenn bereit)

```bash
# 1. PostgreSQL-Datenbank bereitstellen (Render DB, Railway PG, etc.)
export DATABASE_URL=postgresql://user:pass@host:5432/athletik
export ATHLETIK_DB_PATH=/data/athletik.db

# 2. Migration ausführen
cd artifacts/athletik
python tools/migrate_to_pg.py

# 3. DATABASE_URL in Hosting-Dienst als Env-Var setzen → Neustart
```

---

## Deployment-Checkliste

### Vor dem ersten Start

- [ ] `SESSION_SECRET` und `SECRET_KEY` gesetzt (zufällige 32-Byte-Hex-Strings)
- [ ] `ATHLETIK_DATA_DIR` auf persistentes Volume zeigt
- [ ] `APP_ENV=production` gesetzt
- [ ] HTTPS konfiguriert (nginx / Cloud-Dienst)
- [ ] Ersten Superadmin anlegen: `python tools/create_superadmin.py`

### Sicherheits-Checkliste

- [ ] Keine Backup-Dateien im Produktions-Image (`.gitignore` schließt sie aus)
- [ ] `.streamlit/secrets.toml` nicht in Git eingecheckt (`.gitignore` schließt aus)
- [ ] `.env` nicht in Git eingecheckt (`.gitignore` schließt aus)
- [ ] `SESSION_SECRET` ist wirklich zufällig (nicht der Placeholder)

### Backup-Strategie (manuell einrichten)

```bash
# Tägliches SQLite-Backup (Cron auf VPS oder GitHub Action)
sqlite3 /data/athletik.db ".backup /data/uploads/backups/athletik_$(date +%Y%m%d).db"

# Backups älter als 30 Tage löschen
find /data/uploads/backups -name "*.db" -mtime +30 -delete
```

---

## Offene Punkte (nach Go-Live prüfen)

| # | Priorität | Punkt |
|---|---|---|
| 1 | 🟡 | **Session-Invalidierung nach Passwortänderung** — Task #114 in der Aufgabenliste |
| 2 | 🟡 | **Rate-Limiting für Login** — kein Brute-Force-Schutz |
| 3 | 🟡 | **Spieler-Fotos** — aktuell als BLOB in DB; für Skalierung auf Filesystem umstellen |
| 4 | 🟠 | **`use_container_width` deprecated** — Streamlit-Migration nach `width='stretch'` |
| 5 | 🟠 | SQLite → PostgreSQL wenn > 10 gleichzeitige Vereine (Migrations-Skript ist bereit) |
