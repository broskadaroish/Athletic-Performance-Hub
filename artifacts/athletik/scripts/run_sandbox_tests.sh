#!/usr/bin/env bash
# =============================================================================
# run_sandbox_tests.sh — APH Stripe Sandbox End-to-End Testablauf (TEST-001–025)
# =============================================================================
#
# VERWENDUNG
# ----------
#   1. Stripe CLI Webhook-Forwarding starten (in separatem Terminal):
#        stripe listen --forward-to http://localhost:${PORT:-3001}/api/stripe/webhook
#
#   2. API-Server starten:
#        pnpm --filter @workspace/api-server run dev
#
#   3. Env-Variablen setzen (Pflicht für Stripe-CLI-Tests):
#        export APH_VEREIN_ID=1          # Verein-ID aus TEST-001 (nach manueller Registrierung)
#        export APH_SUB_ID=sub_xxx       # Stripe Subscription-ID aus TEST-006 (nach Checkout)
#        export APH_CUSTOMER_ID=cus_xxx  # Stripe Customer-ID aus TEST-006 (nach Checkout)
#
#   4. Skript ausführen:
#        bash artifacts/athletik/scripts/run_sandbox_tests.sh
#
#   Optional — nur bestimmte Tests:
#        bash artifacts/athletik/scripts/run_sandbox_tests.sh 009 010 012
#
# ABHÄNGIGKEITEN
# --------------
#   - stripe CLI (stripe --version)
#   - sqlite3
#   - curl
#   - STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET gesetzt
#   - STRIPE_PRICE_* Env-Vars gesetzt
#
# HINWEIS
# -------
#   Tests 001–004 (Registrierung) und weitere UI-Tests werden als MANUAL markiert
#   und müssen manuell im Browser durchgeführt werden. Danach DB-Werte prüfen.
# =============================================================================

set -euo pipefail

# ── Konfiguration ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

APH_DB="${APH_DB:-$REPO_ROOT/artifacts/athletik/athletik.db}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:${PORT:-3001}/api/stripe/webhook}"

# Verein-IDs und Stripe-IDs — nach manuellen Tests setzen
APH_VEREIN_ID="${APH_VEREIN_ID:-}"
APH_SUB_ID="${APH_SUB_ID:-}"
APH_CUSTOMER_ID="${APH_CUSTOMER_ID:-}"

# Stripe Price-IDs aus Env (aus Replit Secrets / .env)
PRICE_TB_MONAT="${STRIPE_PRICE_TRAINER_BASIC_MONAT:-${STRIPE_PRICE_TRAINER_BASIC_MONTHLY:-}}"
PRICE_TB_YEARLY="${STRIPE_PRICE_TRAINER_BASIC_YEARLY:-}"
PRICE_TP_MONAT="${STRIPE_PRICE_TRAINER_PRO_MONTHLY:-${STRIPE_PRICE_TRAINER_PRO_MONAT:-}}"
PRICE_TP_YEARLY="${STRIPE_PRICE_TRAINER_PRO_YEARLY:-}"
PRICE_VB_MONAT="${STRIPE_PRICE_VEREIN_BASIC_MONTHLY:-${STRIPE_PRICE_VEREIN_BASIC_MONAT:-}}"
PRICE_VB_YEARLY="${STRIPE_PRICE_VEREIN_BASIC_YEARLY:-}"
PRICE_VP_MONAT="${STRIPE_PRICE_VEREIN_PRO_MONTHLY:-${STRIPE_PRICE_VEREIN_PRO_MONAT:-}}"
PRICE_VP_YEARLY="${STRIPE_PRICE_VEREIN_PRO_YEARLY:-}"

# Wartezeit nach Stripe CLI-Befehl (Sekunden) bis Webhook verarbeitet ist
WEBHOOK_WAIT="${WEBHOOK_WAIT:-4}"

# ── Farben & Ausgabe ─────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
MANUAL_COUNT=0
SKIP_COUNT=0

declare -A TEST_RESULTS  # TEST_RESULTS[001]="PASS|FAIL|MANUAL|SKIP"

_header() {
  echo ""
  echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}${BLUE}  TEST-$1: $2${NC}"
  echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${NC}"
}

_pass() {
  local test_nr="$1"; shift
  echo -e "  ${GREEN}✅ PASS${NC} — $*"
  PASS_COUNT=$((PASS_COUNT + 1))
  TEST_RESULTS[$test_nr]="PASS"
}

_fail() {
  local test_nr="$1"; shift
  echo -e "  ${RED}❌ FAIL${NC} — $*"
  FAIL_COUNT=$((FAIL_COUNT + 1))
  TEST_RESULTS[$test_nr]="FAIL"
}

_manual() {
  local test_nr="$1"; shift
  echo -e "  ${YELLOW}🔧 MANUAL${NC} — $*"
  MANUAL_COUNT=$((MANUAL_COUNT + 1))
  TEST_RESULTS[$test_nr]="MANUAL"
}

_skip() {
  local test_nr="$1"; shift
  echo -e "  ${CYAN}⏭  SKIP${NC} — $*"
  SKIP_COUNT=$((SKIP_COUNT + 1))
  TEST_RESULTS[$test_nr]="SKIP"
}

_info() { echo -e "  ${CYAN}ℹ${NC}  $*"; }
_warn() { echo -e "  ${YELLOW}⚠${NC}  $*"; }
_step() { echo -e "  ${BOLD}→${NC} $*"; }

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

# SQL-Abfrage gegen APH-DB
sql() {
  sqlite3 "$APH_DB" "$@"
}

# Einzelnen DB-Wert lesen
sql_val() {
  sqlite3 "$APH_DB" "SELECT $1 FROM $2 WHERE $3;" 2>/dev/null || echo ""
}

# Warten + Info
wait_webhook() {
  _info "Warte ${WEBHOOK_WAIT}s auf Webhook-Verarbeitung..."
  sleep "$WEBHOOK_WAIT"
}

# Stripe CLI-Befehl ausführen und Event-ID extrahieren
stripe_cmd() {
  local output
  output=$(stripe "$@" 2>&1) || true
  echo "$output"
}

# Prüfe ob ein benötigter Wert gesetzt ist
require_var() {
  local var_name="$1"
  local var_val="$2"
  local hint="${3:-}"
  if [[ -z "$var_val" ]]; then
    echo -e "  ${RED}⛔ Fehlende Variable: $var_name${NC}"
    [[ -n "$hint" ]] && echo -e "     Hinweis: $hint"
    return 1
  fi
  return 0
}

# DB-Assertion: Prüfe ob Spalte == erwartetem Wert
assert_eq() {
  local test_nr="$1"
  local label="$2"
  local actual="$3"
  local expected="$4"
  if [[ "$actual" == "$expected" ]]; then
    echo -e "    ${GREEN}✓${NC} $label: '$actual' (erwartet: '$expected')"
    return 0
  else
    echo -e "    ${RED}✗${NC} $label: '$actual' ≠ erwartet '$expected'"
    return 1
  fi
}

# DB-Assertion: Prüfe ob Wert leer ist
assert_null() {
  local test_nr="$1"
  local label="$2"
  local actual="$3"
  if [[ -z "$actual" || "$actual" == "NULL" ]]; then
    echo -e "    ${GREEN}✓${NC} $label: NULL (erwartet: NULL)"
    return 0
  else
    echo -e "    ${RED}✗${NC} $label: '$actual' ≠ erwartet NULL"
    return 1
  fi
}

# DB-Assertion: Prüfe ob Wert nicht leer ist
assert_not_null() {
  local test_nr="$1"
  local label="$2"
  local actual="$3"
  if [[ -n "$actual" && "$actual" != "NULL" ]]; then
    echo -e "    ${GREEN}✓${NC} $label: '$actual' (erwartet: nicht leer)"
    return 0
  else
    echo -e "    ${RED}✗${NC} $label: leer/NULL (erwartet: gesetzt)"
    return 1
  fi
}

# ── Test-Filter ───────────────────────────────────────────────────────────────

REQUESTED_TESTS=("$@")

should_run() {
  local test_nr="$1"
  if [[ ${#REQUESTED_TESTS[@]} -eq 0 ]]; then
    return 0  # Alle Tests ausführen
  fi
  for t in "${REQUESTED_TESTS[@]}"; do
    if [[ "$t" == "$test_nr" ]]; then
      return 0
    fi
  done
  return 1
}

# ═════════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT CHECKS
# ═════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║  APH Stripe Sandbox Tests — run_sandbox_tests.sh         ║${NC}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  DB:          $APH_DB"
echo -e "  Webhook-URL: $WEBHOOK_URL"
echo -e "  Verein-ID:   ${APH_VEREIN_ID:-${YELLOW}(nicht gesetzt)${NC}}"
echo -e "  Sub-ID:      ${APH_SUB_ID:-${YELLOW}(nicht gesetzt)${NC}}"
echo -e "  Customer-ID: ${APH_CUSTOMER_ID:-${YELLOW}(nicht gesetzt)${NC}}"

PREFLIGHT_OK=true

echo ""
echo -e "${BOLD}── Pre-Flight Checks ──────────────────────────────────────────${NC}"

# sqlite3
if command -v sqlite3 &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} sqlite3: $(sqlite3 --version | head -1)"
else
  echo -e "  ${RED}✗${NC} sqlite3 nicht gefunden — bitte installieren"
  PREFLIGHT_OK=false
fi

# DB-Datei
if [[ -f "$APH_DB" ]]; then
  echo -e "  ${GREEN}✓${NC} DB-Datei gefunden: $APH_DB"
else
  echo -e "  ${YELLOW}⚠${NC}  DB-Datei nicht gefunden: $APH_DB"
  echo -e "     (Tests 001–004 müssen zuerst manuell ausgeführt werden)"
  PREFLIGHT_OK=false
fi

# stripe CLI
if command -v stripe &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} stripe CLI: $(stripe --version 2>/dev/null | head -1)"
else
  echo -e "  ${YELLOW}⚠${NC}  stripe CLI nicht gefunden (Tests 009–019 werden übersprungen)"
fi

# curl
if command -v curl &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} curl: $(curl --version | head -1 | cut -d' ' -f1-2)"
else
  echo -e "  ${RED}✗${NC} curl nicht gefunden"
  PREFLIGHT_OK=false
fi

# STRIPE_SECRET_KEY
if [[ -n "${STRIPE_SECRET_KEY:-}" ]]; then
  echo -e "  ${GREEN}✓${NC} STRIPE_SECRET_KEY: gesetzt"
else
  echo -e "  ${YELLOW}⚠${NC}  STRIPE_SECRET_KEY: nicht gesetzt (Stripe-CLI-Tests schlagen fehl)"
fi

# STRIPE_WEBHOOK_SECRET
if [[ -n "${STRIPE_WEBHOOK_SECRET:-}" ]]; then
  echo -e "  ${GREEN}✓${NC} STRIPE_WEBHOOK_SECRET: gesetzt"
else
  echo -e "  ${YELLOW}⚠${NC}  STRIPE_WEBHOOK_SECRET: nicht gesetzt (TEST-021 nicht vollständig)"
fi

# Price-IDs
PRICES_SET=0
for p in "$PRICE_TB_MONAT" "$PRICE_TP_MONAT" "$PRICE_VB_MONAT" "$PRICE_VP_MONAT"; do
  [[ -n "$p" ]] && PRICES_SET=$((PRICES_SET + 1))
done
if [[ $PRICES_SET -ge 4 ]]; then
  echo -e "  ${GREEN}✓${NC} Stripe Price-IDs: alle 4 Monats-Preise gesetzt"
else
  echo -e "  ${YELLOW}⚠${NC}  Stripe Price-IDs: $PRICES_SET/4 Monats-Preise gesetzt (Tests 016–018 eingeschränkt)"
fi

echo ""

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 001–004: REGISTRIERUNG (MANUAL — UI erforderlich)
# ═════════════════════════════════════════════════════════════════════════════

# ── TEST-001 ──────────────────────────────────────────────────────────────────
if should_run "001"; then
  _header "001" "Registrierung TRAINER_BASIC"

  if [[ -z "$APH_VEREIN_ID" ]]; then
    _manual "001" "Manuell: Login-Seite → Registrieren → E-Mail: test.trainerbasic@sandbox.local, Paket: TRAINER_BASIC"
    _info "Nach Registrierung: export APH_VEREIN_ID=<id aus DB>"
    _info "SQL: SELECT id FROM vereine WHERE name='Test Trainer Basic';"
  else
    _step "Prüfe DB-Werte für Verein-ID: $APH_VEREIN_ID"
    FAIL=false
    ROW=$(sql "SELECT lizenztyp, lizenz_status, max_trainer, max_spieler, testphase_bis FROM vereine WHERE id=$APH_VEREIN_ID;" 2>/dev/null || echo "")

    if [[ -z "$ROW" ]]; then
      _fail "001" "Verein mit ID=$APH_VEREIN_ID nicht gefunden"
    else
      IFS='|' read -r v_lizenztyp v_lizenz_status v_max_trainer v_max_spieler v_testphase_bis <<< "$ROW"
      assert_eq "001" "lizenztyp"    "$v_lizenztyp"    "TRAINER_BASIC" || FAIL=true
      assert_eq "001" "lizenz_status" "$v_lizenz_status" "trial"        || FAIL=true
      assert_eq "001" "max_trainer"  "$v_max_trainer"  "1"             || FAIL=true
      assert_eq "001" "max_spieler"  "$v_max_spieler"  "20"            || FAIL=true
      assert_not_null "001" "testphase_bis" "$v_testphase_bis"          || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "001" "DB-Prüfung fehlgeschlagen" || _pass "001" "Alle DB-Werte korrekt (lizenztyp=TRAINER_BASIC, lizenz_status=trial)"
    fi
  fi
fi

# ── TEST-002 ──────────────────────────────────────────────────────────────────
if should_run "002"; then
  _header "002" "Registrierung TRAINER_PRO"

  ROW=$(sql "SELECT lizenztyp, lizenz_status, max_trainer, max_spieler FROM vereine WHERE lizenztyp='TRAINER_PRO' ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "")
  if [[ -z "$ROW" ]]; then
    _manual "002" "Manuell: Registrieren mit E-Mail: test.trainerpro@sandbox.local, Paket: TRAINER_PRO"
  else
    FAIL=false
    IFS='|' read -r v_lizenztyp v_lizenz_status v_max_trainer v_max_spieler <<< "$ROW"
    assert_eq "002" "lizenztyp"    "$v_lizenztyp"   "TRAINER_PRO" || FAIL=true
    assert_eq "002" "lizenz_status" "$v_lizenz_status" "trial"     || FAIL=true
    assert_eq "002" "max_trainer"  "$v_max_trainer"  "1"           || FAIL=true
    assert_null "002" "max_spieler" "$v_max_spieler"               || FAIL=true
    [[ "$FAIL" == "true" ]] && _fail "002" "DB-Prüfung fehlgeschlagen" || _pass "002" "Alle DB-Werte korrekt (TRAINER_PRO, max_spieler=NULL)"
  fi
fi

# ── TEST-003 ──────────────────────────────────────────────────────────────────
if should_run "003"; then
  _header "003" "Registrierung VEREIN_BASIC"

  ROW=$(sql "SELECT lizenztyp, lizenz_status, max_trainer, max_spieler FROM vereine WHERE lizenztyp='VEREIN_BASIC' ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "")
  if [[ -z "$ROW" ]]; then
    _manual "003" "Manuell: Registrieren mit E-Mail: test.vereinbasic@sandbox.local, Paket: VEREIN_BASIC"
  else
    FAIL=false
    IFS='|' read -r v_lizenztyp v_lizenz_status v_max_trainer v_max_spieler <<< "$ROW"
    assert_eq "003" "lizenztyp"   "$v_lizenztyp"  "VEREIN_BASIC" || FAIL=true
    assert_eq "003" "max_trainer" "$v_max_trainer" "2"            || FAIL=true
    assert_eq "003" "max_spieler" "$v_max_spieler" "50"           || FAIL=true
    [[ "$FAIL" == "true" ]] && _fail "003" "DB-Prüfung fehlgeschlagen" || _pass "003" "Alle DB-Werte korrekt (VEREIN_BASIC, max_trainer=2, max_spieler=50)"
  fi
fi

# ── TEST-004 ──────────────────────────────────────────────────────────────────
if should_run "004"; then
  _header "004" "Registrierung VEREIN_PRO"

  ROW=$(sql "SELECT lizenztyp, lizenz_status, max_trainer, max_spieler FROM vereine WHERE lizenztyp='VEREIN_PRO' ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "")
  if [[ -z "$ROW" ]]; then
    _manual "004" "Manuell: Registrieren mit E-Mail: test.vereinpro@sandbox.local, Paket: VEREIN_PRO"
  else
    FAIL=false
    IFS='|' read -r v_lizenztyp v_lizenz_status v_max_trainer v_max_spieler <<< "$ROW"
    assert_eq "004" "lizenztyp"   "$v_lizenztyp"  "VEREIN_PRO" || FAIL=true
    assert_eq "004" "max_trainer" "$v_max_trainer" "15"          || FAIL=true
    assert_null "004" "max_spieler" "$v_max_spieler"             || FAIL=true
    [[ "$FAIL" == "true" ]] && _fail "004" "DB-Prüfung fehlgeschlagen" || _pass "004" "Alle DB-Werte korrekt (VEREIN_PRO, max_trainer=15, max_spieler=NULL)"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 005–008: CHECKOUT (MANUAL — Browser + Stripe Checkout erforderlich)
# ═════════════════════════════════════════════════════════════════════════════

# ── TEST-005 ──────────────────────────────────────────────────────────────────
if should_run "005"; then
  _header "005" "Checkout abbrechen — kein Statuswechsel"

  if [[ -n "$APH_VEREIN_ID" ]]; then
    _step "Prüfe: lizenz_status noch 'trial' und keine Stripe-IDs"
    v_status=$(sql "SELECT lizenz_status FROM vereine WHERE id=$APH_VEREIN_ID;" 2>/dev/null || echo "")
    v_sub=$(sql "SELECT stripe_subscription_id FROM vereine WHERE id=$APH_VEREIN_ID;" 2>/dev/null || echo "")

    _manual "005" "Manuell: Lizenz-Seite → Upgrade-Button → Stripe Checkout → ABBRECHEN"
    _info "Dann: bash $0 005  (erneut ausführen um DB zu prüfen)"
    _info "Aktuell: lizenz_status='$v_status', stripe_subscription_id='${v_sub:-leer}'"
    if [[ "$v_status" == "trial" && -z "$v_sub" ]]; then
      _pass "005" "lizenz_status=trial, kein Stripe-Abo (DB unverändert)"
    else
      _fail "005" "Unerwarteter Zustand nach Abbruch: status='$v_status', sub='$v_sub'"
    fi
  else
    _manual "005" "APH_VEREIN_ID nicht gesetzt — Checkout-Test nach TEST-001 durchführen"
    TEST_RESULTS["005"]="MANUAL"
    MANUAL_COUNT=$((MANUAL_COUNT + 1))
  fi
fi

# ── TEST-006 ──────────────────────────────────────────────────────────────────
if should_run "006"; then
  _header "006" "Checkout erfolgreich — Testkarte 4242"

  if [[ -n "$APH_SUB_ID" && -n "$APH_CUSTOMER_ID" ]]; then
    _step "Prüfe DB-Werte nach erfolgreichem Checkout"
    FAIL=false
    ROW=$(sql "SELECT lizenz_status, zahlungsstatus, stripe_customer_id, stripe_subscription_id, abo_intervall, vertragsbeginn FROM vereine WHERE id=${APH_VEREIN_ID};" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "006" "Keine DB-Daten für Verein-ID=$APH_VEREIN_ID"
    else
      IFS='|' read -r v_status v_zahlung v_cus v_sub v_intervall v_beginn <<< "$ROW"
      assert_eq   "006" "lizenz_status"    "$v_status"   "trial"                   || FAIL=true
      assert_eq   "006" "zahlungsstatus"   "$v_zahlung"  "zahlungsmethode_hinterlegt" || FAIL=true
      assert_not_null "006" "stripe_customer_id" "$v_cus"                          || FAIL=true
      assert_not_null "006" "stripe_subscription_id" "$v_sub"                      || FAIL=true
      assert_not_null "006" "vertragsbeginn" "$v_beginn"                           || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "006" "DB-Prüfung fehlgeschlagen" || _pass "006" "Checkout-Daten korrekt in DB"
    fi
  else
    _manual "006" "Manuell: Lizenz-Seite → Upgrade → Karte 4242 4242 4242 4242, 12/34, CVC 123"
    _info "Danach setzen:"
    _info "  export APH_SUB_ID=sub_…      (aus Stripe Dashboard oder DB)"
    _info "  export APH_CUSTOMER_ID=cus_… (aus Stripe Dashboard oder DB)"
    _info "SQL: SELECT stripe_subscription_id, stripe_customer_id FROM vereine WHERE id=\$APH_VEREIN_ID;"
  fi
fi

# ── TEST-007 ──────────────────────────────────────────────────────────────────
if should_run "007"; then
  _header "007" "Stripe-Rückkehr ohne Cookie — kein automatischer Login"
  _manual "007" "Manuell: success_url in Incognito-Browser öffnen — Login-Formular muss erscheinen"
  _info "Erwartet: HTTP 200, Login-Seite sichtbar, kein Dashboard"
fi

# ── TEST-008 ──────────────────────────────────────────────────────────────────
if should_run "008"; then
  _header "008" "Vertragsanzeige nach Checkout"

  if [[ -n "$APH_VEREIN_ID" ]]; then
    _step "DB-Prüfung: Vertragsdaten vorhanden"
    ROW=$(sql "SELECT lizenztyp, abo_intervall, subscription_current_period_end, vertragsbeginn, lizenz_status FROM vereine WHERE id=$APH_VEREIN_ID;" 2>/dev/null || echo "")
    if [[ -n "$ROW" ]]; then
      IFS='|' read -r v_typ v_intervall v_period_end v_beginn v_status <<< "$ROW"
      _info "lizenztyp=$v_typ, abo_intervall=$v_intervall"
      _info "lizenz_status=$v_status, vertragsbeginn=$v_beginn"
      _info "subscription_current_period_end=$v_period_end"
      _manual "008" "Manuell: Lizenz-Seite prüfen — Paket, Preis, Intervall, Datum stimmen mit DB überein"
    else
      _skip "008" "Keine Vertragsdaten in DB (TEST-006 zuerst durchführen)"
    fi
  else
    _skip "008" "APH_VEREIN_ID nicht gesetzt"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 009–012: KÜNDIGUNG & SUBSCRIPTION LIFECYCLE (STRIPE CLI)
# ═════════════════════════════════════════════════════════════════════════════

# ── TEST-009 ──────────────────────────────────────────────────────────────────
if should_run "009"; then
  _header "009" "Kündigung während Trial (cancel_at_period_end=true)"

  if ! command -v stripe &>/dev/null; then
    _skip "009" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "009" "APH_SUB_ID nicht gesetzt (TEST-006 zuerst ausführen)"
  else
    _step "Stripe CLI: Abo auf cancel-at-period-end setzen"
    stripe subscriptions update "$APH_SUB_ID" --cancel-at-period-end 2>&1 | grep -E "(id:|status:|cancel_at_period_end)" | head -5 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT lizenz_status, cancel_at_period_end, gekuendigt_zum FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "009" "Verein mit sub_id='$APH_SUB_ID' nicht in DB gefunden"
    else
      IFS='|' read -r v_status v_cancel_end v_gekuendigt <<< "$ROW"
      assert_eq       "009" "lizenz_status"       "$v_status"     "cancelled" || FAIL=true
      assert_eq       "009" "cancel_at_period_end" "$v_cancel_end" "1"        || FAIL=true
      assert_not_null "009" "gekuendigt_zum"        "$v_gekuendigt"             || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "009" "Kündigung nicht korrekt verarbeitet" || _pass "009" "Kündigung korrekt: lizenz_status=cancelled, cancel_at_period_end=1"
    fi
  fi
fi

# ── TEST-010 ──────────────────────────────────────────────────────────────────
if should_run "010"; then
  _header "010" "Kündigung rückgängig machen (Reaktivierung)"

  if ! command -v stripe &>/dev/null; then
    _skip "010" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "010" "APH_SUB_ID nicht gesetzt"
  else
    _step "Stripe CLI: cancel_at_period_end auf false setzen"
    stripe subscriptions update "$APH_SUB_ID" --cancel-at-period-end=false 2>&1 | grep -E "(id:|status:|cancel_at_period_end)" | head -5 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT lizenz_status, cancel_at_period_end, gekuendigt_zum FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "010" "Verein mit sub_id='$APH_SUB_ID' nicht in DB gefunden"
    else
      IFS='|' read -r v_status v_cancel_end v_gekuendigt <<< "$ROW"
      assert_eq   "010" "cancel_at_period_end" "$v_cancel_end" "0"   || FAIL=true
      assert_null "010" "gekuendigt_zum"        "$v_gekuendigt"       || FAIL=true
      # lizenz_status darf 'trial' oder 'active' sein
      if [[ "$v_status" == "trial" || "$v_status" == "active" ]]; then
        echo -e "    ${GREEN}✓${NC} lizenz_status: '$v_status' (trial oder active — korrekt)"
      else
        echo -e "    ${RED}✗${NC} lizenz_status: '$v_status' — erwartet 'trial' oder 'active'"
        FAIL=true
      fi
      [[ "$FAIL" == "true" ]] && _fail "010" "Reaktivierung nicht korrekt" || _pass "010" "Reaktivierung korrekt: cancel_at_period_end=0, gekuendigt_zum=NULL"
    fi
  fi
fi

# ── TEST-011 ──────────────────────────────────────────────────────────────────
if should_run "011"; then
  _header "011" "Kündigung bei aktivem Abo (cancel_at_period_end)"

  if ! command -v stripe &>/dev/null; then
    _skip "011" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "011" "APH_SUB_ID nicht gesetzt"
  else
    _step "Stripe CLI: Kündigung bei aktivem Abo"
    stripe subscriptions update "$APH_SUB_ID" --cancel-at-period-end 2>&1 | grep -E "(id:|status:|cancel_at_period_end)" | head -5 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT lizenz_status, cancel_at_period_end, lizenz_bis FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "011" "Verein mit sub_id='$APH_SUB_ID' nicht in DB"
    else
      IFS='|' read -r v_status v_cancel_end v_lizenz_bis <<< "$ROW"
      assert_eq "011" "lizenz_status"       "$v_status"     "cancelled" || FAIL=true
      assert_eq "011" "cancel_at_period_end" "$v_cancel_end" "1"        || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "011" "Kündigung aktives Abo fehlgeschlagen" || _pass "011" "Kündigung korrekt: cancelled, lizenz_bis=$v_lizenz_bis"
    fi

    # Reaktivierung für folgende Tests
    _step "Reaktivierung für Folgetests..."
    stripe subscriptions update "$APH_SUB_ID" --cancel-at-period-end=false 2>&1 | tail -1 || true
    wait_webhook
    _info "Abo reaktiviert"
  fi
fi

# ── TEST-012 ──────────────────────────────────────────────────────────────────
if should_run "012"; then
  _header "012" "subscription.deleted — Zugang sperren, Daten erhalten"

  if ! command -v stripe &>/dev/null; then
    _skip "012" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "012" "APH_SUB_ID nicht gesetzt"
  else
    # Verein-ID für Spieler-Check
    V_ID="${APH_VEREIN_ID:-}"
    SPIELER_COUNT=""
    if [[ -n "$V_ID" ]]; then
      SPIELER_COUNT=$(sql "SELECT COUNT(*) FROM spieler WHERE verein_id=$V_ID;" 2>/dev/null || echo "0")
    fi

    _step "Stripe CLI: Abo sofort beenden"
    stripe subscriptions cancel "$APH_SUB_ID" 2>&1 | grep -E "(id:|status:)" | head -3 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT lizenz_status, zahlungsstatus, cancel_at_period_end FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      # Fallback: per customer_id suchen
      ROW=$(sql "SELECT lizenz_status, zahlungsstatus, cancel_at_period_end FROM vereine WHERE stripe_customer_id='${APH_CUSTOMER_ID:-}';" 2>/dev/null || echo "")
    fi

    if [[ -z "$ROW" ]]; then
      _fail "012" "Verein nach Subscription-Löschung nicht auffindbar"
    else
      IFS='|' read -r v_status v_zahlung v_cancel_end <<< "$ROW"
      assert_eq "012" "lizenz_status"       "$v_status"    "beendet" || FAIL=true
      assert_eq "012" "zahlungsstatus"      "$v_zahlung"   "beendet" || FAIL=true
      assert_eq "012" "cancel_at_period_end" "$v_cancel_end" "0"     || FAIL=true

      if [[ -n "$V_ID" && "$SPIELER_COUNT" != "" ]]; then
        NEW_COUNT=$(sql "SELECT COUNT(*) FROM spieler WHERE verein_id=$V_ID;" 2>/dev/null || echo "0")
        if [[ "$NEW_COUNT" == "$SPIELER_COUNT" ]]; then
          echo -e "    ${GREEN}✓${NC} Spielerdaten erhalten: $NEW_COUNT Spieler (unverändert)"
        else
          echo -e "    ${YELLOW}⚠${NC}  Spieleranzahl geändert: vorher=$SPIELER_COUNT, jetzt=$NEW_COUNT"
        fi
      fi

      [[ "$FAIL" == "true" ]] && _fail "012" "subscription.deleted nicht korrekt verarbeitet" || _pass "012" "Abo beendet: lizenz_status=beendet, Daten erhalten"
    fi

    _warn "TEST-012 hat das Abo beendet — für weitere Tests neues Checkout erforderlich!"
    _info "Wenn weitere Webhook-Tests folgen sollen, bitte neues Abo erstellen und APH_SUB_ID + APH_CUSTOMER_ID neu setzen."
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 013–014: PAYMENT FAILURE & RECOVERY
# ═════════════════════════════════════════════════════════════════════════════

# ── TEST-013 ──────────────────────────────────────────────────────────────────
if should_run "013"; then
  _header "013" "invoice.payment_failed — Status fehlgeschlagen"

  if ! command -v stripe &>/dev/null; then
    _skip "013" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_CUSTOMER_ID" ]]; then
    _skip "013" "APH_CUSTOMER_ID nicht gesetzt"
  else
    _step "Stripe trigger: invoice.payment_failed"
    stripe trigger invoice.payment_failed \
      --add "invoice:customer=$APH_CUSTOMER_ID" 2>&1 | tail -3 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT zahlungsstatus, letzte_zahlung_fehlgeschlagen, lizenz_status FROM vereine WHERE stripe_customer_id='$APH_CUSTOMER_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "013" "Verein mit customer_id='$APH_CUSTOMER_ID' nicht in DB"
    else
      IFS='|' read -r v_zahlung v_letzter v_status <<< "$ROW"
      assert_eq       "013" "zahlungsstatus"               "$v_zahlung" "fehlgeschlagen" || FAIL=true
      assert_not_null "013" "letzte_zahlung_fehlgeschlagen" "$v_letzter"                  || FAIL=true
      # lizenz_status soll aktiv bleiben
      if [[ "$v_status" != "beendet" ]]; then
        echo -e "    ${GREEN}✓${NC} lizenz_status: '$v_status' (kein sofortiger Sperr — korrekt)"
      else
        echo -e "    ${RED}✗${NC} lizenz_status='beendet' — erwartet: Account noch zugänglich"
        FAIL=true
      fi
      [[ "$FAIL" == "true" ]] && _fail "013" "Payment-Failure-Verarbeitung fehlerhaft" || _pass "013" "zahlungsstatus=fehlgeschlagen, Account nicht sofort gesperrt"
    fi
  fi
fi

# ── TEST-014 ──────────────────────────────────────────────────────────────────
if should_run "014"; then
  _header "014" "invoice.paid nach Failure — Lizenz wieder aktiv"

  if ! command -v stripe &>/dev/null; then
    _skip "014" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_CUSTOMER_ID" ]]; then
    _skip "014" "APH_CUSTOMER_ID nicht gesetzt"
  else
    _step "Stripe trigger: invoice.paid (amount_paid=999)"
    stripe trigger invoice.paid \
      --add "invoice:customer=$APH_CUSTOMER_ID" \
      --add "invoice:amount_paid=999" 2>&1 | tail -3 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT zahlungsstatus, lizenz_status, lizenz_bis FROM vereine WHERE stripe_customer_id='$APH_CUSTOMER_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "014" "Verein mit customer_id='$APH_CUSTOMER_ID' nicht in DB"
    else
      IFS='|' read -r v_zahlung v_status v_lizenz_bis <<< "$ROW"
      assert_eq "014" "zahlungsstatus" "$v_zahlung" "bezahlt" || FAIL=true
      assert_eq "014" "lizenz_status"  "$v_status"  "active"  || FAIL=true
      _info "lizenz_bis: $v_lizenz_bis"
      [[ "$FAIL" == "true" ]] && _fail "014" "Payment-Recovery fehlerhaft" || _pass "014" "Zahlung nachgeholt: zahlungsstatus=bezahlt, lizenz_status=active"
    fi
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TEST 015: TRIAL-ENDE SIMULATION (DB-Manipulation)
# ═════════════════════════════════════════════════════════════════════════════

if should_run "015"; then
  _header "015" "Trial-Ende simulieren — Zugang nach Ablauf gesperrt"

  if [[ -z "$APH_VEREIN_ID" ]]; then
    _skip "015" "APH_VEREIN_ID nicht gesetzt"
  else
    _step "Setze testphase_bis auf gestern (Sandbox-Simulation)"
    sql "UPDATE vereine SET testphase_bis = date('now', '-1 day') WHERE id=$APH_VEREIN_ID AND lizenz_status='trial';"
    AFFECTED=$?

    ACTUAL_DATE=$(sql "SELECT testphase_bis FROM vereine WHERE id=$APH_VEREIN_ID;" 2>/dev/null || echo "")
    YESTERDAY=$(date -d "-1 day" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null || echo "")

    if [[ -n "$ACTUAL_DATE" ]]; then
      _info "testphase_bis gesetzt auf: $ACTUAL_DATE"
      _info "lizenz_status in DB: $(sql "SELECT lizenz_status FROM vereine WHERE id=$APH_VEREIN_ID;")"
      _manual "015" "Manuell: App neu laden — Ablauf-Seite muss sichtbar sein (kein Dashboard-Zugriff)"
      _info "WICHTIG: DB-Wert lizenz_status bleibt 'trial' — nur UI-Berechnung ergibt 'expired'"
      _info "Zum Zurücksetzen: sqlite3 $APH_DB \"UPDATE vereine SET testphase_bis=date('now','+30 days') WHERE id=$APH_VEREIN_ID;\""
    else
      _fail "015" "DB-Update fehlgeschlagen oder Verein hat kein trial-Status"
    fi
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 016–018: PAKETWECHSEL
# ═════════════════════════════════════════════════════════════════════════════

# ── TEST-016 ──────────────────────────────────────────────────────────────────
if should_run "016"; then
  _header "016" "Upgrade TRAINER_BASIC → TRAINER_PRO"

  if ! command -v stripe &>/dev/null; then
    _skip "016" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "016" "APH_SUB_ID nicht gesetzt"
  elif [[ -z "$PRICE_TP_MONAT" ]]; then
    _skip "016" "STRIPE_PRICE_TRAINER_PRO_MONTHLY nicht gesetzt"
  else
    _step "Stripe CLI: Upgrade auf TRAINER_PRO ($PRICE_TP_MONAT)"
    stripe subscriptions update "$APH_SUB_ID" \
      --items[0][price]="$PRICE_TP_MONAT" 2>&1 | grep -E "(id:|status:)" | head -3 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT lizenztyp, abo_intervall, lizenz_status FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "016" "Verein nicht in DB gefunden"
    else
      IFS='|' read -r v_typ v_intervall v_status <<< "$ROW"
      assert_eq "016" "lizenztyp"    "$v_typ"       "TRAINER_PRO" || FAIL=true
      assert_eq "016" "abo_intervall" "$v_intervall"  "monat"      || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "016" "Upgrade nicht korrekt verarbeitet" || _pass "016" "Upgrade korrekt: lizenztyp=TRAINER_PRO"
    fi
  fi
fi

# ── TEST-017 ──────────────────────────────────────────────────────────────────
if should_run "017"; then
  _header "017" "Downgrade TRAINER_PRO → TRAINER_BASIC"

  if ! command -v stripe &>/dev/null; then
    _skip "017" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "017" "APH_SUB_ID nicht gesetzt"
  elif [[ -z "$PRICE_TB_MONAT" ]]; then
    _skip "017" "STRIPE_PRICE_TRAINER_BASIC_MONAT nicht gesetzt"
  else
    _step "Stripe CLI: Downgrade auf TRAINER_BASIC ($PRICE_TB_MONAT)"
    stripe subscriptions update "$APH_SUB_ID" \
      --items[0][price]="$PRICE_TB_MONAT" 2>&1 | grep -E "(id:|status:)" | head -3 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT lizenztyp, lizenz_status FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "017" "Verein nicht in DB gefunden"
    else
      IFS='|' read -r v_typ v_status <<< "$ROW"
      assert_eq "017" "lizenztyp" "$v_typ" "TRAINER_BASIC" || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "017" "Downgrade nicht korrekt" || _pass "017" "Downgrade korrekt: lizenztyp=TRAINER_BASIC"
    fi
  fi
fi

# ── TEST-018 ──────────────────────────────────────────────────────────────────
if should_run "018"; then
  _header "018" "Intervallwechsel Monat → Jahr"

  if ! command -v stripe &>/dev/null; then
    _skip "018" "stripe CLI nicht verfügbar"
  elif [[ -z "$APH_SUB_ID" ]]; then
    _skip "018" "APH_SUB_ID nicht gesetzt"
  elif [[ -z "$PRICE_TB_YEARLY" ]]; then
    _skip "018" "STRIPE_PRICE_TRAINER_BASIC_YEARLY nicht gesetzt"
  else
    _step "Stripe CLI: Wechsel auf Jahresabo ($PRICE_TB_YEARLY)"
    stripe subscriptions update "$APH_SUB_ID" \
      --items[0][price]="$PRICE_TB_YEARLY" 2>&1 | grep -E "(id:|status:)" | head -3 || true
    wait_webhook

    FAIL=false
    ROW=$(sql "SELECT abo_intervall, lizenztyp FROM vereine WHERE stripe_subscription_id='$APH_SUB_ID';" 2>/dev/null || echo "")
    if [[ -z "$ROW" ]]; then
      _fail "018" "Verein nicht in DB gefunden"
    else
      IFS='|' read -r v_intervall v_typ <<< "$ROW"
      assert_eq "018" "abo_intervall" "$v_intervall" "jahr"         || FAIL=true
      assert_eq "018" "lizenztyp"     "$v_typ"       "TRAINER_BASIC" || FAIL=true
      [[ "$FAIL" == "true" ]] && _fail "018" "Intervallwechsel fehlgeschlagen" || _pass "018" "Intervallwechsel korrekt: abo_intervall=jahr"
    fi
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 019–021: IDEMPOTENZ & SICHERHEIT
# ═════════════════════════════════════════════════════════════════════════════

# ── TEST-019 ──────────────────────────────────────────────────────────────────
if should_run "019"; then
  _header "019" "Idempotenz — doppelter Webhook wird ignoriert"

  if ! command -v stripe &>/dev/null; then
    _skip "019" "stripe CLI nicht verfügbar"
  else
    _step "Letzte verarbeitete Event-ID aus stripe_events lesen"
    LAST_EVT=$(sql "SELECT event_id FROM stripe_events ORDER BY processed_at DESC LIMIT 1;" 2>/dev/null || echo "")

    if [[ -z "$LAST_EVT" ]]; then
      _skip "019" "Keine Events in stripe_events — erst andere Tests ausführen"
    else
      _info "Letzte Event-ID: $LAST_EVT"
      COUNT_BEFORE=$(sql "SELECT COUNT(*) FROM stripe_events WHERE event_id='$LAST_EVT';" 2>/dev/null || echo "0")

      _step "Stripe CLI: Event erneut senden (resend)"
      stripe events resend "$LAST_EVT" 2>&1 | tail -3 || true
      wait_webhook

      COUNT_AFTER=$(sql "SELECT COUNT(*) FROM stripe_events WHERE event_id='$LAST_EVT';" 2>/dev/null || echo "0")

      if [[ "$COUNT_AFTER" == "1" ]]; then
        _pass "019" "Event-ID '$LAST_EVT' genau einmal in stripe_events (Idempotenz korrekt)"
      else
        _fail "019" "Event-ID $COUNT_AFTER mal in stripe_events — erwartet: genau 1"
      fi
    fi
  fi
fi

# ── TEST-020 ──────────────────────────────────────────────────────────────────
if should_run "020"; then
  _header "020" "Ungültige Signatur → HTTP 400"

  _step "curl: Webhook mit gefälschter Signatur"
  HTTP_CODE=$(curl -s -o /tmp/aph_test020_response.txt -w "%{http_code}" \
    -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -H "stripe-signature: t=1234567890,v1=invalidsignaturehere000000000000000000000000000000000000000000000000" \
    -d '{"id":"evt_fake_020","type":"checkout.session.completed","data":{"object":{}}}' \
    --connect-timeout 5 \
    2>/dev/null || echo "000")

  RESPONSE=$(cat /tmp/aph_test020_response.txt 2>/dev/null || echo "")

  if [[ "$HTTP_CODE" == "400" ]]; then
    _pass "020" "HTTP 400 zurückgegeben (ungültige Signatur korrekt abgewiesen)"
    _info "Response: $RESPONSE"
  elif [[ "$HTTP_CODE" == "000" ]]; then
    _fail "020" "Kein HTTP-Response — API-Server nicht erreichbar unter $WEBHOOK_URL"
    _info "Ist der API-Server gestartet? pnpm --filter @workspace/api-server run dev"
  else
    _fail "020" "HTTP $HTTP_CODE — erwartet: 400. Response: $RESPONSE"
  fi
fi

# ── TEST-021 ──────────────────────────────────────────────────────────────────
if should_run "021"; then
  _header "021" "Fehlendes STRIPE_WEBHOOK_SECRET → HTTP 503 (Fail-Closed)"

  _manual "021" "Manuell: STRIPE_WEBHOOK_SECRET aus Env entfernen, API-Server neu starten"
  _info "Dann curl:"
  _info "  curl -s -o /dev/null -w \"%{http_code}\" -X POST $WEBHOOK_URL \\"
  _info "    -H 'Content-Type: application/json' \\"
  _info "    -d '{\"id\":\"evt_test\",\"type\":\"checkout.session.completed\"}'"
  _info "Erwartet: HTTP 503"
  _info "Anschließend: STRIPE_WEBHOOK_SECRET wiederherstellen, Server neu starten"

  # Alternativer automatischer Test: kein Stripe-Signature Header senden → 400
  _step "Automatisiert prüfbar: kein stripe-signature Header → HTTP 400"
  HTTP_CODE=$(curl -s -o /tmp/aph_test021_response.txt -w "%{http_code}" \
    -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"id":"evt_test_021","type":"test"}' \
    --connect-timeout 5 \
    2>/dev/null || echo "000")

  if [[ "$HTTP_CODE" == "400" ]]; then
    _info "Ohne Signatur-Header: HTTP 400 (Fail-Closed bestätigt)"
  elif [[ "$HTTP_CODE" == "000" ]]; then
    _warn "API-Server nicht erreichbar — Test übersprungen"
  else
    _info "HTTP $HTTP_CODE (ohne Signatur-Header)"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# TESTS 022–023: SESSION / COOKIE
# ═════════════════════════════════════════════════════════════════════════════

if should_run "022"; then
  _header "022" "success_url ohne Cookie — kein automatischer Login"
  _manual "022" "Manuell: success_url aus Checkout in Incognito-Browser öffnen"
  _info "Erwartet: Login-Formular sichtbar, HTTP 200, kein Dashboard"
fi

if should_run "023"; then
  _header "023" "Browser-Reload mit Cookie — Session bleibt erhalten"
  _manual "023" "Manuell: Nach Login F5 drücken — Dashboard muss direkt sichtbar sein"
  _info "Erwartet: kein erneuter Login-Dialog, Session-Cookie noch vorhanden"
fi

# ═════════════════════════════════════════════════════════════════════════════
# TEST 024: SUPERADMIN-DASHBOARD (DB-Check + MANUAL für UI)
# ═════════════════════════════════════════════════════════════════════════════

if should_run "024"; then
  _header "024" "Superadmin-Vertragsstatus — DB-Übersicht"

  _step "DB-Übersicht aller Vereine (Lizenzstatus)"
  echo ""
  sql "
    SELECT printf('%-4s', id) AS id,
           printf('%-25s', SUBSTR(name,1,25)) AS name,
           printf('%-14s', lizenztyp) AS lizenztyp,
           printf('%-12s', lizenz_status) AS lizenz_status,
           printf('%-15s', zahlungsstatus) AS zahlungsstatus,
           CASE WHEN stripe_customer_id IS NOT NULL THEN '✓' ELSE '—' END AS stripe
    FROM vereine
    ORDER BY id;
  " 2>/dev/null | sed 's/^/    /' || _warn "DB nicht erreichbar"
  echo ""
  _manual "024" "Manuell: Als Superadmin einloggen → 💳 Lizenzverwaltung — Status-Badges prüfen"
fi

# ═════════════════════════════════════════════════════════════════════════════
# TEST 025: KEINE DOPPEL-SUBSCRIPTION (DB-Check)
# ═════════════════════════════════════════════════════════════════════════════

if should_run "025"; then
  _header "025" "Keine Doppel-Subscription nach erneutem Checkout"

  if [[ -n "$APH_CUSTOMER_ID" ]]; then
    _step "DB-Check: Genau eine Customer-Zeile pro customer_id"
    COUNT=$(sql "SELECT COUNT(*) FROM vereine WHERE stripe_customer_id='$APH_CUSTOMER_ID';" 2>/dev/null || echo "0")
    if [[ "$COUNT" == "1" ]]; then
      _pass "025" "Genau 1 Verein mit customer_id='$APH_CUSTOMER_ID' (keine Duplikate)"
    else
      _fail "025" "$COUNT Vereine mit gleicher customer_id — Duplikate!"
    fi
    _manual "025" "Manuell: Stripe Dashboard → Customer $APH_CUSTOMER_ID → Subscriptions: genau 1 aktives Abo"
  else
    _skip "025" "APH_CUSTOMER_ID nicht gesetzt"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# BONUS: DB-SCHEMA-CHECK (keine Testnummer — Hilfsprüfung)
# ═════════════════════════════════════════════════════════════════════════════

if should_run "schema" || [[ ${#REQUESTED_TESTS[@]} -eq 0 ]]; then
  echo ""
  echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}${BLUE}  SCHEMA-CHECK: Pflicht-Spalten in vereine${NC}"
  echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${NC}"

  REQUIRED_COLS=(
    "lizenz_status" "zahlungsstatus" "stripe_customer_id" "stripe_subscription_id"
    "testphase_bis" "lizenz_bis" "abo_intervall" "cancel_at_period_end"
    "subscription_current_period_end" "vertragsbeginn" "letzte_zahlung_fehlgeschlagen"
    "gekuendigt_zum"
  )

  SCHEMA=$(sql "PRAGMA table_info(vereine);" 2>/dev/null || echo "")
  SCHEMA_FAIL=false

  for col in "${REQUIRED_COLS[@]}"; do
    if echo "$SCHEMA" | grep -q "|$col|"; then
      echo -e "    ${GREEN}✓${NC} $col"
    else
      echo -e "    ${RED}✗${NC} $col — FEHLT!"
      SCHEMA_FAIL=true
    fi
  done

  if [[ "$SCHEMA_FAIL" == "false" ]]; then
    echo -e "  ${GREEN}✅ Alle 12 Pflicht-Spalten vorhanden${NC}"
  else
    echo -e "  ${RED}❌ Schema unvollständig — stripe.ts ensureDbExtensions() aufrufen${NC}"
  fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═════════════════════════════════════════════════════════════════════════════

TOTAL=$((PASS_COUNT + FAIL_COUNT + MANUAL_COUNT + SKIP_COUNT))

echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║  ERGEBNIS                                                ║${NC}"
echo -e "${BOLD}${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${BLUE}║${NC}  ${GREEN}PASS${NC}:   $PASS_COUNT"
echo -e "${BOLD}${BLUE}║${NC}  ${RED}FAIL${NC}:   $FAIL_COUNT"
echo -e "${BOLD}${BLUE}║${NC}  ${YELLOW}MANUAL${NC}: $MANUAL_COUNT  (Browser/UI erforderlich)"
echo -e "${BOLD}${BLUE}║${NC}  ${CYAN}SKIP${NC}:   $SKIP_COUNT   (Variablen fehlen / nicht verfügbar)"
echo -e "${BOLD}${BLUE}║${NC}  Gesamt: $TOTAL"
echo -e "${BOLD}${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"

if [[ $FAIL_COUNT -eq 0 && $PASS_COUNT -gt 0 ]]; then
  echo -e "${BOLD}${BLUE}║${NC}  ${GREEN}${BOLD}STATUS: ALLE AUTOMATISIERTEN TESTS BESTANDEN ✅${NC}"
elif [[ $FAIL_COUNT -gt 0 ]]; then
  echo -e "${BOLD}${BLUE}║${NC}  ${RED}${BOLD}STATUS: $FAIL_COUNT TEST(S) FEHLGESCHLAGEN ❌${NC}"
else
  echo -e "${BOLD}${BLUE}║${NC}  ${YELLOW}STATUS: Nur manuelle Tests — keine automatisierten Ergebnisse${NC}"
fi

echo -e "${BOLD}${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${BLUE}║  Einzelergebnisse:                                       ║${NC}"

for nr in "001" "002" "003" "004" "005" "006" "007" "008" "009" "010" "011" "012" "013" "014" "015" "016" "017" "018" "019" "020" "021" "022" "023" "024" "025"; do
  RESULT="${TEST_RESULTS[$nr]:-—}"
  case "$RESULT" in
    PASS)   ICON="${GREEN}✅ PASS  ${NC}" ;;
    FAIL)   ICON="${RED}❌ FAIL  ${NC}" ;;
    MANUAL) ICON="${YELLOW}🔧 MANUAL${NC}" ;;
    SKIP)   ICON="${CYAN}⏭  SKIP  ${NC}" ;;
    *)      ICON="   —     " ;;
  esac
  echo -e "${BOLD}${BLUE}║${NC}  TEST-$nr: $ICON"
done

echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [[ $MANUAL_COUNT -gt 0 ]]; then
  echo -e "${YELLOW}Manuelle Tests:${NC}"
  echo -e "  Nach manueller Durchführung Skript erneut mit gesetzten Variablen starten:"
  echo -e "  ${CYAN}export APH_VEREIN_ID=<id>${NC}"
  echo -e "  ${CYAN}export APH_SUB_ID=sub_…${NC}"
  echo -e "  ${CYAN}export APH_CUSTOMER_ID=cus_…${NC}"
  echo -e "  ${CYAN}bash artifacts/athletik/scripts/run_sandbox_tests.sh${NC}"
  echo ""
fi

# Exit-Code: 1 wenn Tests fehlgeschlagen
[[ $FAIL_COUNT -eq 0 ]] && exit 0 || exit 1
