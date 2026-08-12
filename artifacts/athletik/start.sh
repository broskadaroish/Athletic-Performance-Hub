#!/bin/bash
# Stellt sicher, dass Port 8082 frei ist, bevor Streamlit startet.
# Wartet in einer Schleife bis zu 10 Sekunden, damit schnelle Restarts
# (z. B. durch Replit Forced-Restart) keinen "Port not available"-Fehler auslösen.
fuser -k 8082/tcp 2>/dev/null || true
for i in $(seq 1 20); do
  fuser 8082/tcp 2>/dev/null || break
  sleep 0.5
done
exec streamlit run app.py --server.port 8082
