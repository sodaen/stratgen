.PHONY: help venv install dev run fmt lint test changelog-latest snapshot clean

help:
	@echo "Targets:"
	@echo "  install, dev, run, fmt, lint, test, changelog-latest, snapshot, clean"
	@echo "  reviews-dump, reviews-dump-json, reviews-stats, self-play, phase3-mini"
	@echo "  llm-ping, llm-enhance-smoke, phase3-autotune"
	@echo "  learn-scan-http, learn-stats-http, graph-from-learn, graph-stats, phase2-graph"
	@echo "  ensure-deck-tables, ingest-pptx FILE=..., learn-styles, styles-stats, pptx-preview DECK_ID=.. [LIMIT=5]"

venv:
	@test -d .venv || python3 -m venv .venv

install: venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt 2>/dev/null || true
	. .venv/bin/activate && pip install -r requirements-img.txt 2>/dev/null || true

dev:
	. .venv/bin/activate && $(UVICORN) $(APP) --reload --host $(HOST) --port $(PORT)

run:
	. .venv/bin/activate && $(UVICORN) $(APP) --host $(HOST) --port $(PORT)

fmt:
	. .venv/bin/activate && ruff check --fix .
	. .venv/bin/activate && black .

lint:
	. .venv/bin/activate && ruff check .

test:
	. .venv/bin/activate && pytest -q

changelog-latest:
	@echo "# Datei CHANGELOG.md hier im Chat posten – dann bin ich up to date."
	. .venv/bin/activate && $(PY) ingest.py changelog-latest

snapshot:
	. .venv/bin/activate && $(PY) ingest.py snapshot

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true

## Stoppt zuverlässig (PIDFILE, pkill-Fallback, fuser)
stop:
	@echo ">> Stoppe gunicorn auf $(HOST):$(PORT)"
	@if [ -f "$(PIDFILE)" ]; then \
	  PID=$$(cat "$(PIDFILE)"); \
	  echo "  killing master PID $$PID ..."; \
	  kill -TERM $$PID 2>/dev/null || true; \
	  sleep 1; \
	  kill -KILL $$PID 2>/dev/null || true; \
	fi
	@rm -f "$(PIDFILE)"
	@pkill -f "$(BIN)/gunicorn .*$(APP) .*$(HOST):$(PORT)" 2>/dev/null || true
	@fuser -k $(PORT)/tcp 2>/dev/null || true
	@make status

restart: stop start

status:
	@lsof -nP -iTCP:$(PORT) -sTCP:LISTEN || echo "✅ Port $(PORT) frei"
