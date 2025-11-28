.PHONY: ensure-deck-tables ingest-pptx learn-styles styles-stats pptx-preview

ensure-deck-tables:
	@. .venv/bin/activate && ./.venv/bin/python scripts/ensure_deck_tables.py

ingest-pptx:
	@test -n "$(FILE)" || (echo "Bitte FILE=pfad/zur/datei.pptx angeben" && exit 2)
	@curl -s -X POST "$(API)/pptx/ingest" -H "Content-Type: application/json" -d '{"path":"$(FILE)","source":"manual"}' | jq .

learn-styles:
	@curl -s -X POST "$(API)/pptx/learn?name=default" | jq .

styles-stats:
	@. .venv/bin/activate && ./.venv/bin/python scripts/styles_stats.py | jq .

pptx-preview:
	@test -n "$(DECK_ID)" || (echo "Bitte DECK_ID=<id> setzen (z.B. via: sqlite3 data/projects.sqlite 'select id from decks limit 1')" && exit 2)
	@LIMIT=$(if $(LIMIT),$(LIMIT),5); curl -s "$(API)/pptx/preview/$(DECK_ID)?limit=$${LIMIT}" | jq .
