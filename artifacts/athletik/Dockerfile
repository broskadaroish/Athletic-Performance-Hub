# ============================================================
# Athletik App — Docker-Image für VPS / Self-Hosting
#
# Bauen:
#   docker build -t athletik-app .
#
# Starten (Entwicklung):
#   docker run -p 8080:8080 \
#     -e APP_ENV=production \
#     -e SESSION_SECRET=mein-secret \
#     -v $(pwd)/data:/data \
#     athletik-app
#
# Mit docker-compose: siehe docker-compose.yml
# ============================================================

FROM python:3.11-slim

# Systemabhängigkeiten (libpq für psycopg2, gcc für Kompilierung)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Abhängigkeiten zuerst (Docker-Cache-Optimierung)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode
COPY . .

# Startskript ausführbar machen
RUN chmod +x start.sh

# Verzeichnisse anlegen (werden beim Start aus start.sh auch angelegt)
RUN mkdir -p uploads/logos uploads/spielerbilder uploads/pdf \
             uploads/exports uploads/backups uploads/docs logs

# Standardport (überschreibbar per -e PORT=XXXX)
ENV PORT=8082 \
    APP_ENV=production \
    ATHLETIK_DATA_DIR=/data

EXPOSE 8082

# Gesundheitscheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8082}/_stcore/health')" || exit 1

CMD ["bash", "start.sh"]
