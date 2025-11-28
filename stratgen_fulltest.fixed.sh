#!/usr/bin/env bash
# Stratgen Fulltest (100 Slides) – robuste Variante mit Routen-Autodetect
# - Erkennt /projects/save vs. /content/generate
# - Fix: robustes PID-Parsing (.project.id | .proj.id | .id | .project_id)
# - Fix: Generate verwendet $PID (kein undefiniertes $project_id)
# - Fix: Knowledge-Timeouts (scan=300s, embed_local=600s)
set -Eeuo pipefail
IFS=$'\n\t'
trap 'ec=$?; echo "[FAIL] line $LINENO exit $ec" >&2; exit $ec' ERR

# ===== Konfiguration =====
: "${BASE:=http://127.0.0.1:8011}"
: "${ORG:=ShiftMind GmbH}"
: "${TOPIC:=KI-gestützter Shopfloor-Assistent für Fertigungsbetriebe}"
: "${SLIDES:=100}"
: "${K:=5}"              # K fürs RAG (falls akzeptiert)
: "${API_KEY:=}"         # optional

# ===== Hilfsfunktionen =====
RUN_DIR="$(mktemp -d -t stratgen_fulltest.XXXXXX)"
OPENAPI="$RUN_DIR/openapi.json"
mkdir -p "$RUN_DIR"

HDR=(-H 'content-type: application/json')
if [[ -n "${API_KEY}" ]]; then
  HDR+=(-H "Authorization: Bearer ${API_KEY}")
fi

get()  { curl -fsS --max-time "${3:-30}" "${HDR[@]}" "$BASE$1"; }
post() { curl -fsS --retry 2 --retry-delay 1 --max-time "${3:-120}" -H 'content-type: application/json' "${HDR[@]}" "$BASE$1" -d "$2"; }

have_path() {
  # Prüft, ob ein Pfad in .paths existiert (OpenAPI wird gecached)
  if [[ ! -s "$OPENAPI" ]]; then
    curl -fsS --max-time 30 "${HDR[@]}" "$BASE/openapi.json" >"$OPENAPI"
  fi
  jq -e --arg p "$1" '.paths | has($p)' "$OPENAPI" >/dev/null 2>&1
}

j() { jq -er "$1"; } # JSON extractor (fail on null/false)

# ===== Briefing =====
read -r -d '' BRIEFING <<'BRI'
ShiftMind ist ein KI-gestützter Shopfloor-Assistent für Fertigungsbetriebe.
Ziel: Reaktionszeiten und Stillstände senken, Erstlösungsquote erhöhen.
Anwender: Produktionsleitung, Schichtführung, Instandhaltung.
Use-Cases: Störungsbehebung (guided), Wartung (Checklisten), Onboarding (Lernpfade).
Architektur: Edge/On-Prem, DSGVO, Audit-Log, Integrationen in MES/ERP/CMMS.
GTM: Co-Creation-Piloten, IIoT-Partner, messbare OEE-Verbesserung.
BRI

echo "[1/9] Health"
get "/health" 30 | jq .
get "/ops/diag" 30 | jq .

echo "[2/9] Knowledge (scan + embed_local)"
post "/knowledge/scan" '{}' 300 | jq .
if have_path "/knowledge/embed_local"; then
  post "/knowledge/embed_local" '{}' 600 | jq .
else
  echo "[warn] /knowledge/embed_local fehlt – überspringe Embedding."
fi
echo "   ok"

echo "[3/9] Projekt anlegen /projects/save (mit OUTLINE + FACTS, falls verfügbar)"
PID="proj-$(date +%s)-$$"   # Vorab-ID als Fallback
OUTLINE_JSON=$(jq -nc --arg t "ShiftMind – KI-gestützter Shopfloor-Assistent" '
  {title:$t, sections:[
    {title:"Executive Summary",bullets:["Ziel: Reaktionszeiten & Stillstände senken; Erstlösungsquote erhöhen","Scope: Mittelstand – Produktionsleitung, Schichtführung, Instandhaltung","Ansatz: Sprach-/Text-Assistenz, dokumentiert Arbeit automatisch"]},
    {title:"Problem & Kontext",bullets:["Zersplittertes Schichtwissen; Medienbrüche","Reaktive Störungsbearbeitung (lange MTTR)","Onboarding dauert lange; Know-how in Köpfen"]},
    {title:"Use Cases (Werksalltag)",bullets:["Störung X: Schritt-für-Schritt","Wartung: dynamische Checklisten","Onboarding: Lernpfade an der Maschine"]},
    {title:"Produktkern ShiftMind",bullets:["Bündelt Wissen/Historik; Next-Best-Actions","Multimodal; Edge offline-fähig","Automatische Dokumentation; Übergaben an MES/ERP/CMMS"]},
    {title:"Architektur & Integrationen",bullets:["Privacy-by-Design; DSGVO","APIs/Webhooks; Rollen/SSO","Audit-Log & revisionssicher"]},
    {title:"Safety & Change Management",bullets:["Freigabeprozesse; 4-Augen-Prinzip","Betriebsrat einbinden; Verantwortlichkeiten","Fallbacks & Rollback bei Modell-Updates"]},
    {title:"GTM",bullets:["Piloten mit Leitwerken","Partnerschaften: Systemhäuser/IIoT","Story: messbare OEE-Verbesserung"]},
    {title:"Monetarisierung",bullets:["SaaS pro Werk/Seat; Module","Staffelungen; Services","ROI durch Stillstandsreduktion"]},
    {title:"KPI-System",bullets:["Aktive Nutzung/Schicht; Reaktionszeit","Stillstandsminuten; MTTR","Onboarding-Zeit; Zufriedenheit"]},
    {title:"Risiken & Mitigations",bullets:["Datenqualität/Schnittstellen","Akzeptanz am Shopfloor","Regulatorik/Safety"]},
    {title:"Roadmap (90/180/360 Tage)",bullets:["Pilot (2 Linien)","Safety-Gate Releases, Edge-Härtung","Internationalisierung"]}
  ]}
')
FACTS_JSON=$(jq -nc --arg b "$BRIEFING" '{bullets:[], sources:[], briefing:$b}')

SAVE_PAYLOAD=$(jq -nc --arg org "$ORG" --arg topic "$TOPIC" --argjson outline "$OUTLINE_JSON" --argjson facts "$FACTS_JSON" --arg pid "$PID" --argjson slides "$SLIDES" '
  {project_id:$pid, customer_name:$org, topic:$topic, outline:$outline, facts:$facts, slides:$slides}
')

if have_path "/projects/save"; then
  SAVE_RESP=$(post "/projects/save" "$SAVE_PAYLOAD" 60)
  echo "$SAVE_RESP" | jq .
  PID_FROM_RESP=$(echo "$SAVE_RESP" | jq -r '.project.id // .proj.id // .id // .project_id // empty')
  if [[ -n "$PID_FROM_RESP" ]]; then PID="$PID_FROM_RESP"; fi
elif have_path "/projects"; then
  SAVE_RESP=$(post "/projects" "$SAVE_PAYLOAD" 60)
  echo "$SAVE_RESP" | jq .
  PID_FROM_RESP=$(echo "$SAVE_RESP" | jq -r '.project.id // .proj.id // .id // .project_id // empty')
  if [[ -n "$PID_FROM_RESP" ]]; then PID="$PID_FROM_RESP"; fi
else
  echo "[i] Kein /projects/save – benutze One‑Shot /content/generate."
fi

echo "   project_id: $PID"

echo "[4/9] Projekt-Generate /projects/{id}/generate (oder One‑Shot)"
GEN_PAYLOAD=$(jq -nc --argjson slides "$SLIDES" --argjson k "${K}" '{k:$k, slides:$slides}')

if have_path "/projects/{id}/generate"; then
  post "/projects/$PID/generate" "$GEN_PAYLOAD" 180 | jq .
elif have_path "/content/generate"; then
  # One‑Shot ohne persistenten Project-Record
  ONE=$(jq -nc --arg org "$ORG" --arg topic "$TOPIC" --arg b "$BRIEFING" --argjson slides "$SLIDES" --argjson k "${K}" '
     {org:$org, topic:$topic, briefing:$b, slides:$slides, k:$k}
  ')
  post "/content/generate" "$ONE" 240 | jq .
else
  echo "[warn] Weder /projects/{id}/generate noch /content/generate gefunden."
fi

echo "[5/9] Verfeinerung (review/critique/autotune) – best effort"
if have_path "/projects/{id}/review"; then
  post "/projects/$PID/review" '{}' 60 | jq .
fi
if have_path "/projects/{id}/critique"; then
  post "/projects/$PID/critique" '{}' 60 | jq .
fi
if have_path "/projects/{id}/autotune"; then
  post "/projects/$PID/autotune" '{}' 60 | jq .
fi

echo "[6/9] Assets/Preview (best effort)"
if have_path "/projects/{id}/assets/refresh"; then
  post "/projects/$PID/assets/refresh" '{}' 90 | jq .
fi

echo "[7/9] Snapshot (best effort)"
if have_path "/projects/{id}/snapshot"; then
  post "/projects/$PID/snapshot" '{}' 60 | jq .
fi

echo "[8/9] PPTX rendern"
if have_path "/projects/{id}/export/pptx"; then
  EXP=$(post "/projects/$PID/export/pptx" '{}' 240 | jq .)
  echo "$EXP"
  URL=$(echo "$EXP" | jq -r '.url // empty')
  PATH_JSON=$(echo "$EXP" | jq -r '.path // empty')
  if [[ -n "$URL" ]]; then
    echo "[9/9] Download"
    NAME="$(printf '%s_%sslides_%(%Y%m%d-%H%M%S)T.pptx' "${TOPIC// /_}" "$SLIDES" -1)"
    curl -fsS "$BASE$URL" -o "$NAME"
    echo "   DONE → $(pwd)/$NAME"
  elif [[ -n "$PATH_JSON" && -f "$PATH_JSON" ]]; then
    echo "   Lokale Datei: $PATH_JSON"
  fi
else
  echo "[warn] Kein /projects/{id}/export/pptx – Export übersprungen."
fi

echo "[OK] stratgen_fulltest finished"
