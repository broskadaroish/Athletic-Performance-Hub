"""
Server-seitige Dateitypprüfung anhand Magic Bytes.

st.file_uploader(type=[...]) prüft nur die Dateiendung (client-seitig, leicht
manipulierbar). Diese Klasse liest die ersten Bytes der Datei und gleicht sie
mit bekannten Signaturen ab.

Verwendung:
    from utils.file_magic import validate_image, validate_pdf

    ok, error = validate_image(file_bytes, max_mb=2)
    if not ok:
        st.error(error)
"""

from __future__ import annotations

# MIME-Typ → Liste von (Signatur-Bytes, Byte-Offset)
_SIGNATURES: dict[str, list[tuple[bytes, int]]] = {
    "image/jpeg": [
        (b"\xff\xd8\xff\xe0", 0),
        (b"\xff\xd8\xff\xe1", 0),
        (b"\xff\xd8\xff\xdb", 0),
        (b"\xff\xd8\xff\xee", 0),
    ],
    "image/png":  [(b"\x89PNG\r\n\x1a\n", 0)],
    "image/gif":  [(b"GIF87a", 0), (b"GIF89a", 0)],
    "image/webp": [(b"RIFF", 0)],   # zusätzlich: Bytes 8–11 = b"WEBP"
    "application/pdf": [(b"%PDF-", 0)],
    # ZIP-basierte Office-Formate (xlsx, docx) für Exporte
    "application/zip": [(b"PK\x03\x04", 0)],
}

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_PDF_TYPES   = {"application/pdf"}
ALLOWED_EXCEL_TYPES = {"application/zip"}   # xlsx ist intern ein ZIP


def detect_mime(data: bytes) -> str | None:
    """Erkennt den MIME-Typ anhand der ersten Bytes. Gibt None zurück wenn unbekannt."""
    for mime, sigs in _SIGNATURES.items():
        for sig, offset in sigs:
            if len(data) >= offset + len(sig) and data[offset:offset + len(sig)] == sig:
                # WebP-Sonderfall: Bytes 8–11 müssen "WEBP" sein
                if mime == "image/webp":
                    if len(data) >= 12 and data[8:12] == b"WEBP":
                        return mime
                    continue
                return mime
    return None


def validate_image(file_bytes: bytes, max_mb: int = 5) -> tuple[bool, str]:
    """Prüft ob die Bytes ein erlaubtes Bildformat darstellen.

    Returns:
        (True, "")               bei Erfolg
        (False, Fehlermeldung)   bei Fehler
    """
    if not file_bytes:
        return False, "Leere Datei."
    if len(file_bytes) > max_mb * 1024 * 1024:
        return False, f"Datei zu groß (max. {max_mb} MB erlaubt)."
    mime = detect_mime(file_bytes)
    if mime not in ALLOWED_IMAGE_TYPES:
        detected = mime or "unbekannt"
        return False, (
            f"Ungültiges Dateiformat (erkannt: {detected}). "
            "Erlaubt: JPEG, PNG, GIF, WebP."
        )
    return True, ""


def validate_pdf(file_bytes: bytes, max_mb: int = 20) -> tuple[bool, str]:
    """Prüft ob die Bytes eine gültige PDF-Datei darstellen."""
    if not file_bytes:
        return False, "Leere Datei."
    if len(file_bytes) > max_mb * 1024 * 1024:
        return False, f"Datei zu groß (max. {max_mb} MB erlaubt)."
    mime = detect_mime(file_bytes)
    if mime not in ALLOWED_PDF_TYPES:
        detected = mime or "unbekannt"
        return False, (
            f"Ungültiges Dateiformat (erkannt: {detected}). "
            "Erlaubt: PDF."
        )
    return True, ""


def validate_excel(file_bytes: bytes, max_mb: int = 10) -> tuple[bool, str]:
    """Prüft ob die Bytes eine gültige Excel-Datei (xlsx) darstellen."""
    if not file_bytes:
        return False, "Leere Datei."
    if len(file_bytes) > max_mb * 1024 * 1024:
        return False, f"Datei zu groß (max. {max_mb} MB erlaubt)."
    mime = detect_mime(file_bytes)
    if mime not in ALLOWED_EXCEL_TYPES:
        detected = mime or "unbekannt"
        return False, (
            f"Ungültiges Dateiformat (erkannt: {detected}). "
            "Erlaubt: Excel (.xlsx)."
        )
    return True, ""
