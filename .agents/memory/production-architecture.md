---
name: Produktionsarchitektur aphsystem.de
description: Wie und wo die App in Produktion läuft — kritisch für alle Deployment-Entscheidungen
---

# Produktionsarchitektur aphsystem.de

## Laufzeitumgebungen — strikt getrennt

| Umgebung | Ort | Datenbank |
|----------|-----|-----------|
| **Entwicklung** | Replit-Workspace | `artifacts/athletik/athletik.db` (SQLite, lokal) |
| **Produktion** | Ubuntu-VPS, Docker Compose | `/data/athletik.db` (SQLite, persistentes Docker-Volume) |

Replit Secrets stehen dem Produktionsserver **NICHT** automatisch zur Verfügung.

## Produktionsserver-Details

- **Docker Compose** unter `/opt/aphsystem/artifacts/athletik/docker-compose.yml`
- **DB-Pfad:** `ATHLETIK_DB_PATH=/data/athletik.db` (Docker Volume `athletik_data`)
- **Domain:** `https://aphsystem.de`
- **SMTP:** `smtp.ionos.de:465`, Absender `noreply@aphsystem.de`, Reply-To `support@aphsystem.de`

## Environment-Variablen auf Produktionsserver

Liegen in `/opt/aphsystem/artifacts/athletik/.env` (chmod 600, in .gitignore).
docker-compose.yml leitet sie via `${VAR}` an den Container weiter.

Pflicht-Variablen auf dem Server:
- `APP_BASE_URL=https://aphsystem.de`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SUPPORT_EMAIL`
- `SESSION_SECRET`, `SECRET_KEY`

## Kritische Regeln (niemals verletzen)

1. `/data/athletik.db` niemals löschen, überschreiben oder neu initialisieren
2. `docker compose down -v` niemals ausführen (löscht Volume + alle Daten)
3. Docker-Volume `athletik_data` bei jedem Update erhalten lassen
4. Produktionsdaten (Benutzer, Vereine, Trainer, Spieler, Tests, Pläne, Lizenzen) niemals löschen
5. Neue Umgebungsvariablen müssen in docker-compose.yml UND in der Server-.env eingetragen werden — Replit-Secrets allein reichen nicht

## Bekannte Inkonsistenzen im Repo (noch nicht behoben)

1. **docker-compose.yml fehlen SMTP + APP_BASE_URL** — wurden manuell auf Server ergänzt, aber Quell-Datei im Repo ist veraltet
2. **start.sh hardcodiert Port 8082** — Docker erwartet aber PORT=8080 (EXPOSE + docker-compose); in Produktion funktioniert es nur, weil nginx auf 8082 umleitet oder der Server eine abweichende start.sh hat
3. **config.py liest `SMTP_USER`** — email_service.py liest `SMTP_USERNAME` — unterschiedliche Variablennamen; email_service.py ist korrekt, config.py-Eintrag ist verwaist

**Why:** Ohne dieses Wissen würden neue Env-Vars nur in Replit Secrets gesetzt und auf dem Produktionsserver fehlen — das war die ursprüngliche Ursache für ausbleibende E-Mails.
