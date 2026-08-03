#!/bin/bash
# Stellt sicher, dass Port 8082 frei ist, bevor Streamlit startet.
fuser -k 8082/tcp 2>/dev/null || true
sleep 0.5
exec streamlit run app.py --server.port 8082
