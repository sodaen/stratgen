.PHONY: ensure-deck-tables ingest-pptx learn-styles styles-stats pptx-preview

ensure-deck-tables:
	@. .venv/bin/activate && python - <<'PY'
import os, sqlite3
os.makedirs("data", exist_ok=True)
con = sqlite3.connect("data/projects.sqlite", timeout=30, isolation_level=None)
cur = con.cursor()
cur.execute("PRAGMA journal_mode=WAL")
cur.execute("PRAGMA synchronous=NORMAL")
cur.executescript("""
CREATE TABLE IF NOT EXISTS decks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL,
  source TEXT,
  meta_json TEXT
);
CREATE TABLE IF NOT EXISTS deck_slides(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deck_id INTEGER NOT NULL,
  idx INTEGER NOT NULL DEFAULT 0,
  kind TEXT,
  title TEXT,
  bullets_json TEXT,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_deck_slides_deck ON deck_slides(deck_id);
CREATE INDEX IF NOT EXISTS idx_deck_slides_kind ON deck_slides(kind);
CREATE TABLE IF NOT EXISTS style_profiles(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at INTEGER NOT NULL,
  name TEXT NOT NULL,
  profile_json TEXT NOT NULL
);
""")
con.commit()
con.close()
print("[OK] ensure-deck-tables: Schema & WAL bereit")
PY

# Benutzung: make ingest-pptx FILE=data/raw/deck.pptx
ingest-pptx:
	@FILE="$(FILE)"; test -n "$$FILE" || { echo 'Bitte FILE=pfad/zum/deck.pptx angeben'; exit 2; }
	@curl -s -X POST "http://127.0.0.1:8001/pptx/ingest" \
		-H "Content-Type: application/json" \
		-d "{\"path\":\"$${FILE}\",\"source\":\"manual\"}" | jq .

learn-styles:
	@curl -s -X POST "http://127.0.0.1:8001/pptx/learn?name=default" | jq .

styles-stats:
	@. .venv/bin/activate && ./.venv/bin/python scripts/styles_stats.py | jq .

# Benutzung: make pptx-preview DECK_ID=1 [LIMIT=5]
pptx-preview:
	@DECK_ID="$(DECK_ID)"; LIMIT="$(LIMIT)"; test -n "$$DECK_ID" || { echo 'Bitte DECK_ID angeben'; exit 2; }
	@test -n "$$LIMIT" || LIMIT=5; \
	curl -s "http://127.0.0.1:8001/pptx/preview/$${DECK_ID}?limit=$${LIMIT}" | jq .
