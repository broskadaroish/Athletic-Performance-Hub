#!/usr/bin/env python3
"""
Tägliches automatisches Datenbank-Backup.

Verwendung:
    python tools/backup.py

Konfiguration via Umgebungsvariablen (alle optional):
    ATHLETIK_DB_PATH      — Pfad zur SQLite-Datenbank
    ATHLETIK_DATA_DIR     — Datenwurzel (Standard: App-Verzeichnis)
    BACKUP_RETENTION_DAYS — Backups älter als N Tage löschen (Standard: 30)
    S3_BUCKET             — S3-kompatibler Bucket für externen Upload (optional)
    S3_ENDPOINT_URL       — Endpoint-URL für S3-kompatible Dienste (optional)
    AWS_ACCESS_KEY_ID     — S3-Zugangsdaten (optional)
    AWS_SECRET_ACCESS_KEY — S3-Zugangsdaten (optional)

Exit-Codes:
    0 — Backup erfolgreich
    1 — Backup fehlgeschlagen
"""

import os
import sys
import shutil
import sqlite3
import logging
import datetime
from pathlib import Path

# ── Logging (stdout für Cloud-Dienste + optional Datei) ──────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] backup: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("backup")


# ── Konfiguration ─────────────────────────────────────────────────────────────
def _resolve_config() -> dict:
    """Lese alle relevanten Env-Vars und leite Pfade ab."""
    # Verzeichnis-Wurzel: entweder ATHLETIK_DATA_DIR oder App-Verzeichnis
    app_dir = Path(__file__).resolve().parent.parent  # artifacts/athletik/
    data_dir = Path(os.environ.get("ATHLETIK_DATA_DIR", str(app_dir)))

    db_path = Path(os.environ.get("ATHLETIK_DB_PATH", str(data_dir / "athletik.db")))
    backup_dir = data_dir / "uploads" / "backups"
    retention_days = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))

    # S3-Konfiguration (alle leer → kein Upload)
    s3_bucket = os.environ.get("S3_BUCKET", "").strip()
    s3_endpoint = os.environ.get("S3_ENDPOINT_URL", "").strip()
    aws_key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
    s3_enabled = bool(s3_bucket and aws_key and aws_secret)

    return {
        "db_path": db_path,
        "backup_dir": backup_dir,
        "retention_days": retention_days,
        "s3_bucket": s3_bucket,
        "s3_endpoint": s3_endpoint,
        "s3_enabled": s3_enabled,
    }


# ── Backup erstellen ──────────────────────────────────────────────────────────
def _create_backup(db_path: Path, backup_dir: Path) -> Path:
    """
    Erstellt ein konsistentes SQLite-Backup mit der nativen Online-Backup-API.
    Gibt den Pfad zur Backup-Datei zurück.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Datenbank nicht gefunden: {db_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().strftime("%Y-%m-%d")
    backup_filename = f"athletik_{today}.db"
    backup_path = backup_dir / backup_filename

    # Wenn heute schon ein Backup existiert, vorherige Version aufbewahren
    if backup_path.exists():
        ts = datetime.datetime.now().strftime("%H%M%S")
        backup_path = backup_dir / f"athletik_{today}_{ts}.db"
        log.info("Heutiges Backup existiert bereits — speichere als: %s", backup_path.name)

    # SQLite Online-Backup-API: konsistenter Snapshot auch bei laufenden Writes
    log.info("Erstelle Backup: %s → %s", db_path, backup_path)
    src_conn = sqlite3.connect(str(db_path))
    try:
        dst_conn = sqlite3.connect(str(backup_path))
        try:
            src_conn.backup(dst_conn, pages=100)
            dst_conn.execute("PRAGMA integrity_check")
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    size_kb = backup_path.stat().st_size / 1024
    log.info("Backup erfolgreich: %s (%.1f KB)", backup_path.name, size_kb)
    return backup_path


# ── Integrität prüfen ─────────────────────────────────────────────────────────
def _verify_backup(backup_path: Path) -> None:
    """Öffnet das Backup und führt integrity_check durch."""
    conn = sqlite3.connect(str(backup_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        if result[0] != "ok":
            raise RuntimeError(f"Integritätsprüfung fehlgeschlagen: {result[0]}")
        log.info("Integritätsprüfung bestanden: %s", backup_path.name)
    finally:
        conn.close()


# ── Alte Backups löschen ──────────────────────────────────────────────────────
def _purge_old_backups(backup_dir: Path, retention_days: int) -> None:
    """Löscht Backup-Dateien, die älter als retention_days Tage sind."""
    if retention_days <= 0:
        log.info("Automatisches Löschen deaktiviert (BACKUP_RETENTION_DAYS=%d)", retention_days)
        return

    cutoff = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    deleted = 0
    for f in sorted(backup_dir.glob("athletik_*.db")):
        mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            f.unlink()
            log.info("Altes Backup gelöscht: %s (geändert: %s)", f.name, mtime.strftime("%Y-%m-%d"))
            deleted += 1

    if deleted:
        log.info("%d alte Backup(s) gelöscht (Aufbewahrung: %d Tage)", deleted, retention_days)
    else:
        log.info("Keine alten Backups zu löschen (Aufbewahrung: %d Tage)", retention_days)


# ── S3-Upload (optional) ──────────────────────────────────────────────────────
def _upload_to_s3(backup_path: Path, cfg: dict) -> None:
    """Lädt das Backup in einen S3-kompatiblen Bucket hoch."""
    try:
        import boto3  # type: ignore
    except ImportError:
        log.warning("boto3 nicht installiert — S3-Upload übersprungen. "
                    "Installation: pip install boto3")
        return

    s3_key = f"backups/{backup_path.name}"
    kwargs: dict = {
        "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        "region_name": os.environ.get("AWS_REGION", "auto"),
    }
    if cfg["s3_endpoint"]:
        kwargs["endpoint_url"] = cfg["s3_endpoint"]

    try:
        s3 = boto3.client("s3", **kwargs)
        log.info("Lade Backup hoch: s3://%s/%s", cfg["s3_bucket"], s3_key)
        s3.upload_file(str(backup_path), cfg["s3_bucket"], s3_key)
        log.info("S3-Upload erfolgreich: s3://%s/%s", cfg["s3_bucket"], s3_key)
    except Exception as exc:  # noqa: BLE001
        # Fehler beim S3-Upload → als Warnung loggen, nicht als Fatal
        log.error("S3-Upload fehlgeschlagen: %s", exc)


# ── Hauptfunktion ─────────────────────────────────────────────────────────────
def main() -> int:
    """
    Führt den vollständigen Backup-Prozess aus.
    Gibt 0 zurück bei Erfolg, 1 bei Fehler.
    """
    log.info("══════════════════════════════════════════")
    log.info("Athletik Backup-Job gestartet")

    try:
        cfg = _resolve_config()
        log.info("Datenbank:   %s", cfg["db_path"])
        log.info("Backup-Ziel: %s", cfg["backup_dir"])
        log.info("Aufbewahrung: %d Tage", cfg["retention_days"])
        log.info("S3-Upload:   %s", "aktiviert" if cfg["s3_enabled"] else "deaktiviert")

        # 1. Backup erstellen
        backup_path = _create_backup(cfg["db_path"], cfg["backup_dir"])

        # 2. Integrität prüfen
        _verify_backup(backup_path)

        # 3. Alte Backups löschen
        _purge_old_backups(cfg["backup_dir"], cfg["retention_days"])

        # 4. Optional: S3-Upload
        if cfg["s3_enabled"]:
            _upload_to_s3(backup_path, cfg)

        log.info("Backup-Job abgeschlossen ✓")
        log.info("══════════════════════════════════════════")
        return 0

    except FileNotFoundError as exc:
        log.error("Datenbank nicht gefunden — Backup abgebrochen: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        log.error("Backup fehlgeschlagen: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
