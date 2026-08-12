# Railway Environment Variables — Athletic Performance Hub

Vollständige Checkliste aller Umgebungsvariablen für das Railway-Deployment
auf **aphsystem.de**. Abgeglichen gegen `config.py` und `email_service.py`
(Stand: SCHRITT 6). Im Railway-Dashboard unter
`Project → Service → Settings → Variables` eintragen.

---

## 🔴 PFLICHT — Produktionseinsatz ohne diese Variablen nicht sicher

| Variable | Wert / Beschreibung | Standard im Code |
|---|---|---|
| `APP_BASE_URL` | `https://aphsystem.de` | `http://localhost:8082` — führt zu ungültigen Reset-Links! |
| `SESSION_SECRET` | Zufälliger String ≥ 32 Zeichen | `dev-secret-change-in-production` — **im Repo sichtbar!** |
| `SECRET_KEY` | Zufälliger String ≥ 32 Zeichen (**anderer** als SESSION_SECRET) | `dev-key-change-in-production` — **im Repo sichtbar!** |
| `SMTP_PASSWORD` | IONOS-Passwort für `noreply@aphsystem.de` | Nicht gesetzt → E-Mail-Versand schlägt fehl |

> **Warum APP_BASE_URL kritisch ist:**
> Passwort-Reset- und E-Mail-Verifikations-Links werden aus `APP_BASE_URL` gebaut
> (`email_service.py` + `app.py → _app_base_url()`).
> Ist die Variable nicht gesetzt, greift `config.py` auf `http://localhost:8082` zurück —
> Links in E-Mails zeigen dann auf die falsche Umgebung → Token-Mismatch.
>
> **Erzeugt sicher:** `openssl rand -hex 32`

---

## 🟡 EMPFOHLEN — Für stabile Produktion setzen

| Variable | Empfohlener Wert | Standard | Quelle |
|---|---|---|---|
| `APP_ENV` | `production` | `development` | config.py |
| `ATHLETIK_DB_PATH` | `/mnt/data/athletik.db` | `athletik.db` im Arbeitsverzeichnis (**nicht persistent!**) | config.py / database.py |
| `ATHLETIK_DATA_DIR` | `/mnt/data` | Verzeichnis der `app.py`-Datei | config.py |
| `BEHIND_PROXY` | `true` | `false` | config.py |
| `TRUSTED_PROXIES` | `127.0.0.1` oder Railway-interne IP | `127.0.0.1` | config.py |
| `SUPERADMIN_EMAIL` | `admin@aphsystem.de` (Superadmin-Adresse) | `""` (leer) | config.py |

> **BEHIND_PROXY-Parser:** `os.environ.get("BEHIND_PROXY","false").lower() == "true"`.
> Akzeptiert: `true`, `True`, `TRUE` (alle Groß-/Kleinschreibungen durch `.lower()`).
> Nicht akzeptiert: `1`, `yes`, `on`.
>
> **ATHLETIK_DB_PATH — Volume zwingend:**
> Railway-Container sind ephemer — ohne Volume-Mount gehen alle Daten bei Redeploy verloren.
> `Railway → Service → Storage → Add Volume → Mount Path: /mnt/data`

---

## 🟢 OPTIONAL — Mit sinnvollen Standardwerten vorbelegt

### E-Mail / SMTP

> ⚠️ **Wichtig — zwei Konfigurationsquellen:**
> `email_service.py` und `config.py` lesen teilweise **unterschiedliche** Variablennamen
> mit unterschiedlichen Defaults. Für den tatsächlichen E-Mail-Versand ist **`email_service.py`
> maßgeblich**. `config.py` SMTP-Werte sind derzeit für künftige Erweiterungen reserviert.

| Variable | Standard in `email_service.py` | Standard in `config.py` | Hinweis |
|---|---|---|---|
| `SMTP_HOST` | `smtp.ionos.de` | `smtp.gmail.com` | email_service.py ist aktiver Versandweg |
| `SMTP_PORT` | `465` (SSL) | `587` | email_service.py ist aktiver Versandweg |
| `SMTP_USERNAME` | `noreply@aphsystem.de` | — (nicht gelesen) | **Nur email_service.py** |
| `SMTP_USER` | — (nicht gelesen) | `""` | **Nur config.py** (reserviert) |
| `SMTP_FROM` | `noreply@aphsystem.de` | Wert von SMTP_USER | email_service.py bestimmt Absender |
| `SUPPORT_EMAIL` | `support@aphsystem.de` | — | In E-Mail-Texten |

### Session & Login

| Variable | Standard | Beschreibung |
|---|---|---|
| `SESSION_IDLE_TIMEOUT` | `3600` (1 Stunde) | Sekunden bis zur Auto-Abmeldung bei Inaktivität (app.py) |
| `SESSION_MAX_LIFETIME` | `86400` (24 Stunden) | Maximale Session-Dauer in Sekunden (app.py) |
| `SESSION_TIMEOUT_MINUTES` | `60` | Session-Timeout in Minuten (config.py) |
| `MAX_LOGIN_VERSUCHE` | `5` | Fehlversuche bis zur Konto-Sperrung |
| `LOGIN_SPERRE_MINUTEN` | `15` | Sperrzeit nach zu vielen Fehlversuchen |

### Upload-Limits

| Variable | Standard | Beschreibung |
|---|---|---|
| `MAX_UPLOAD_MB` | `10` | Allgemeines Upload-Limit in MB |
| `MAX_LOGO_MB` | `2` | Limit für Vereinslogos |
| `MAX_SPIELERBILD_MB` | `5` | Limit für Spielerfotos |
| `MAX_DOC_MB` | `10` | Limit für Dokumente |

### Backup

| Variable | Standard | Beschreibung |
|---|---|---|
| `BACKUP_RETENTION_DAYS` | `30` | Aufbewahrungszeit für lokale Backups |
| `S3_BUCKET` | `""` (leer = deaktiviert) | S3-Bucket-Name für externes Backup |
| `S3_ENDPOINT_URL` | `""` | S3-Endpunkt (z. B. für Cloudflare R2) |
| `AWS_ACCESS_KEY_ID` | `""` | S3-Zugriffsschlüssel |
| `AWS_SECRET_ACCESS_KEY` | `""` | S3-Geheimschlüssel |
| `AWS_REGION` | `""` | S3-Region |

### Wartungsmodus

| Variable | Standard | Beschreibung |
|---|---|---|
| `MAINTENANCE_MODE` | `0` | `1` = App zeigt Wartungsseite |
| `MAINTENANCE_MESSAGE` | `""` | Text der Wartungsmeldung |

### Sonstiges

| Variable | Standard | Beschreibung |
|---|---|---|
| `PORT` | `8082` | Port, auf dem Streamlit lauscht |
| `LOG_LEVEL` | `WARNING` (production) / `INFO` (dev) | Logging-Level |
| `DATABASE_URL` | — | PostgreSQL-URL (Railway PostgreSQL-Service injiziert automatisch) |

---

## Stripe-Integration (nur wenn Stripe-Zahlungen aktiv)

| Variable | Standard | Beschreibung |
|---|---|---|
| `STRIPE_SECRET_KEY` | `""` | Stripe Secret Key (sk_live_…) |
| `STRIPE_PUBLISHABLE_KEY` | `""` | Stripe Publishable Key (pk_live_…) |
| `STRIPE_WEBHOOK_SECRET` | `""` | Webhook-Signing-Secret |
| `STRIPE_PRICE_BASIC_MONAT` | `""` | Stripe Price-ID Basis monatlich |
| `STRIPE_PRICE_BASIC_JAHR` | `""` | Stripe Price-ID Basis jährlich |
| `STRIPE_PRICE_PRO_MONAT` | `""` | Stripe Price-ID Pro monatlich |
| `STRIPE_PRICE_PRO_JAHR` | `""` | Stripe Price-ID Pro jährlich |

---

## Schnell-Setup (minimale Produktionskonfiguration)

```bash
# 1. Pflicht-Secrets generieren
openssl rand -hex 32   # → SESSION_SECRET
openssl rand -hex 32   # → SECRET_KEY  (anderen Wert als SESSION_SECRET verwenden)

# 2. Railway Variables setzen
APP_BASE_URL      = https://aphsystem.de
SESSION_SECRET    = <Wert aus Schritt 1>
SECRET_KEY        = <Wert aus Schritt 1>
SMTP_PASSWORD     = <IONOS-Passwort>

# 3. Empfohlene Produktionswerte
APP_ENV           = production
ATHLETIK_DB_PATH  = /mnt/data/athletik.db
ATHLETIK_DATA_DIR = /mnt/data
BEHIND_PROXY      = true
SUPERADMIN_EMAIL  = <eigene Superadmin-Adresse>
LOG_LEVEL         = WARNING

# 4. Volume einrichten
# Railway → Service → Storage → Add Volume → Mount Path: /mnt/data
```

---

## Token-Mismatch zwischen Umgebungen vermeiden

**Problem:** Passwort-Reset-Token wird in Datenbank A erzeugt,
aber der Link öffnet Server B (andere DB) → Token ungültig.

**Lösung:** Jede Umgebung hat eine eigene `APP_BASE_URL` und eine eigene Datenbank.

| Umgebung | APP_BASE_URL | Datenbank |
|---|---|---|
| Replit Dev | `https://<dev-domain>/athletik/app` | Replit-Workspace SQLite |
| Railway Prod | `https://aphsystem.de` | `/mnt/data/athletik.db` (Volume) |

Links in E-Mails zeigen immer auf die Umgebung, in der der Token erzeugt wurde.

---

## Schnell-Test nach Deployment

1. `https://aphsystem.de` öffnen → Login-Seite erscheint
2. „Passwort vergessen?" → E-Mail anfordern
3. E-Mail prüfen: Link muss mit `https://aphsystem.de/?reset=…` beginnen
4. Link öffnen → Passwort-Reset-Formular erscheint (kein Token-Mismatch)

---

*Abgeglichen gegen: `config.py`, `email_service.py`, `app.py`, `database.py` — SCHRITT 6 / Task #176*
