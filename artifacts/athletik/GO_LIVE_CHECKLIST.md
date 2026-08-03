# Bruce Football — Go-Live Checkliste

Stand: 2026-08-03  
Für Fragen: info@brucefootball.de

---

## Legende
- [ ] Offen
- [x] Erledigt
- [~] Nicht zutreffend / optional

---

## 1. Infrastruktur & Hosting

### Pflicht vor Go-Live
- [ ] **Hosting-Dienst gewählt** (Render.com empfohlen — `render.yaml` ist bereit)
- [ ] **Persistentes Volume** eingebunden: `ATHLETIK_DATA_DIR` zeigt auf `/data` (Render Disk)
- [ ] **Custom Domain** konfiguriert und DNS eingetragen (`brucefootball.de`)
- [ ] **HTTPS** aktiv (automatisch bei Render/Railway — bei VPS: Certbot einrichten)
- [ ] **Landing Page** (`artifacts/landing`) deployed und erreichbar unter `https://brucefootball.de/`
- [ ] **App** (`artifacts/athletik`) deployed und erreichbar unter `https://brucefootball.de/app`
- [ ] **API Server** (`artifacts/api-server`) deployed und erreichbar unter `https://brucefootball.de/api`

### Empfohlen
- [ ] CDN für statische Assets konfiguriert (Cloudflare Free Tier)
- [ ] Uptime-Monitoring eingerichtet (UptimeRobot / Better Uptime — kostenlos)
- [ ] Automatisches Backup-Cron eingerichtet (Task #131)

---

## 2. Datenbank

- [ ] `ATHLETIK_DB_PATH` auf persistentes Volume gesetzt (`/data/athletik.db`)
- [ ] PostgreSQL-Datenbank provisioniert (für Landing-API: Render PostgreSQL Free)
- [ ] DB-Tabellen `contacts` und `leads` angelegt (automatisch beim API-Start)
- [ ] Erster Superadmin angelegt: `python tools/create_superadmin.py`
- [ ] Admin-Login getestet
- [ ] Testdaten aus Entwicklungsphase entfernt

---

## 3. Sicherheit

- [ ] **`SESSION_SECRET`** auf langen Zufallswert gesetzt:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **`SECRET_KEY`** ebenfalls gesetzt (wie SESSION_SECRET)
- [ ] **`APP_ENV=production`** gesetzt
- [ ] Kein Backup-Dateien (`*.db`, `backup_*.py`) im Produktions-Image
- [ ] `.streamlit/secrets.toml` nicht in Git eingecheckt
- [ ] `.env` nicht in Git eingecheckt
- [ ] Alle Test-Passwörter geändert (Superadmin, Demo-Accounts)
- [ ] Passwort-Richtlinie kommuniziert (min. 8 Zeichen empfohlen)

---

## 4. Datenschutz & Rechtliches (DSGVO)

- [ ] **Impressum** korrekt ausgefüllt (Firmenname, Adresse, Handelsregister, USt-IdNr.)
- [ ] **Datenschutzerklärung** auf aktuellem Stand (Anwalt prüfen empfohlen)
- [ ] **Nutzungsbedingungen** von Anwalt geprüft und freigegeben
- [ ] **Cookie-Banner** implementiert und funktionsfähig (nur notwendige Cookies)
- [ ] Datenschutzbeauftragter benannt (bei ≥ 20 Mitarbeitern mit regelmäßiger Verarbeitung)
- [ ] **Auftragsverarbeitungsvertrag (AVV)** mit Hosting-Anbieter abgeschlossen:
  - Render: https://render.com/docs/data-processing-agreement
  - Railway: https://railway.com/legal/dpa
- [ ] Datenschutzerklärung enthält korrekten Verantwortlichen
- [ ] Löschkonzept für Spielerdaten dokumentiert

---

## 5. Anwendung

- [ ] **Session-Timeout** konfiguriert (`SESSION_TIMEOUT_MINUTES=60`)
- [ ] **Wartungsmodus** getestet (`MAINTENANCE_MODE=1` → Landing Page zeigt Wartungsseite)
- [ ] **Rate-Limiting für Login** implementiert (Task #132 — vor Go-Live prüfen)
- [ ] Login-Ablauf vollständig getestet (Login → App → Logout)
- [ ] Passwort-zurücksetzen-Flow getestet
- [ ] PDF-Generierung getestet (Spielerprofil-PDF, Trainingsplan-PDF)
- [ ] Excel-Export getestet
- [ ] Vereinslogo-Upload getestet
- [ ] Spielerfoto-Upload getestet

---

## 6. Landing Page

- [ ] Alle Links funktionsfähig (Navigation, CTAs, Impressum, Datenschutz)
- [ ] Kontaktformular getestet (Email-Empfang prüfen)
- [ ] Demo-Anfrage-Formular getestet (Lead in DB gespeichert)
- [ ] Cookie-Banner: Zustimmung gespeichert, Banner verschwindet
- [ ] Cookie-Banner: Ablehnen-Funktion vorhanden
- [ ] Alle Preispläne korrekt
- [ ] Mobile Ansicht geprüft (iOS + Android)
- [ ] SEO: Meta-Tags, Title, Description, OG-Tags gesetzt
- [ ] Favicon konfiguriert

---

## 7. E-Mail-Versand

- [ ] **E-Mail-Provider** konfiguriert (Mailgun / Postmark / SendGrid empfohlen):
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` als Env-Vars setzen
- [ ] Willkommens-E-Mail bei neuer Demo-Anfrage (automatisch oder manuell)
- [ ] Kontaktformular-Eingang wird an `info@brucefootball.de` weitergeleitet
- [ ] Passwort-zurücksetzen-E-Mail getestet (aktuell: manuell über Admin)
- [ ] SPF + DKIM für Absender-Domain konfiguriert (Anti-Spam)

---

## 8. Stripe-Vorbereitung (vor Monetarisierung)

- [ ] Stripe-Account erstellt (stripe.com)
- [ ] `STRIPE_SECRET_KEY` (Test-Modus) als Env-Var gesetzt
- [ ] `STRIPE_WEBHOOK_SECRET` als Env-Var gesetzt
- [ ] Preispläne in Stripe angelegt:
  - Starter: XX €/Monat
  - Professional: XX €/Monat
  - Enterprise: Individuell
- [ ] Webhook-Endpunkt in Stripe Dashboard eingetragen: `https://brucefootball.de/api/stripe/webhook`
- [ ] Stripe-Signaturprüfung in `artifacts/api-server/src/routes/stripe.ts` aktiviert
- [ ] Checkout-Flow end-to-end getestet (Test-Karte: 4242 4242 4242 4242)

---

## 9. Monitoring & Logging

- [ ] **Logs** werden gesammelt (Render/Railway: automatisch in Dashboard)
- [ ] **Error-Alerting** eingerichtet (Sentry Free / Render Alerts)
- [ ] **Uptime-Monitoring** aktiv (UptimeRobot: 5-Minuten-Checks)
- [ ] Log-Rotation konfiguriert (Render: automatisch — VPS: `logrotate`)
- [ ] **Health-Check-URLs** erreichbar:
  - App: `https://brucefootball.de/app`
  - API: `https://brucefootball.de/api/healthz`

---

## 10. Backup & Recovery

- [ ] Tägliches SQLite-Backup konfiguriert (Task #131 oder manuell per Cron)
- [ ] Backup-Test: Backup wiederherstellen und App starten
- [ ] Recovery-Prozess dokumentiert
- [ ] Backup-Dateien werden außerhalb des App-Containers gespeichert

---

## 11. Abnahme & Launch

- [ ] Beta-Test mit 1–2 Pilotvereinen abgeschlossen
- [ ] Kritische Bugs behoben
- [ ] Performance unter Last getestet (mind. 10 gleichzeitige Nutzer)
- [ ] Vollständige Datenschutzfolgenabschätzung (DSFA) bei Bedarf
- [ ] **Go/No-Go Entscheidung** vom Verantwortlichen freigegeben
- [ ] Ankündigungs-E-Mail an Pilotvereine gesendet
- [ ] DNS-TTL vor Launch auf niedrigen Wert gesetzt (300s) für schnelles Rollback

---

## Umgebungsvariablen Checkliste

Alle folgenden Env-Vars müssen in der Produktionsumgebung gesetzt sein:

| Variable | Beispiel | Pflicht |
|---|---|---|
| `APP_ENV` | `production` | ✓ |
| `PORT` | automatisch | ✓ |
| `SESSION_SECRET` | 32-Byte-Hex | ✓ |
| `SECRET_KEY` | 32-Byte-Hex | ✓ |
| `ATHLETIK_DATA_DIR` | `/data` | ✓ |
| `ATHLETIK_DB_PATH` | `/data/athletik.db` | ✓ |
| `DATABASE_URL` | `postgresql://...` | ✓ (für API) |
| `LOG_LEVEL` | `WARNING` | empfohlen |
| `SESSION_TIMEOUT_MINUTES` | `60` | empfohlen |
| `MAINTENANCE_MODE` | `0` | empfohlen |
| `MAINTENANCE_MESSAGE` | — | optional |
| `STRIPE_SECRET_KEY` | `sk_live_...` | bei Stripe |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | bei Stripe |
| `SMTP_HOST` | `smtp.mailgun.org` | bei E-Mail |
| `SMTP_PORT` | `587` | bei E-Mail |
| `SMTP_USER` | `noreply@...` | bei E-Mail |
| `SMTP_PASS` | — | bei E-Mail |

---

## Schnellstart: Render.com

```bash
# 1. Repository auf GitHub pushen
git add . && git commit -m "Production ready" && git push

# 2. Render Dashboard → New Web Service → GitHub Repo
#    render.yaml wird automatisch erkannt

# 3. Secrets in Render Dashboard setzen:
#    SESSION_SECRET, SECRET_KEY, DATABASE_URL

# 4. Ersten Superadmin anlegen:
#    Render → Web Service → Shell
#    python tools/create_superadmin.py

# 5. Health Check prüfen:
#    curl https://brucefootball.de/api/healthz
```
