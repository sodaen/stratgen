.PHONY: reviews-dump reviews-dump-json reviews-stats self-play phase3-mini \
        llm-ping llm-enhance-smoke phase3-autotune \
        learn-scan-http learn-stats-http graph-from-learn graph-stats phase2-graph \
        ollama-pull-basic ollama-pull-creative

# Reviews (rein Python, keine sqlite3-CLI)
reviews-dump:
	@. .venv/bin/activate && ./.venv/bin/python scripts/reviews_dump.py

reviews-dump-json:
	@. .venv/bin/activate && ./.venv/bin/python scripts/reviews_dump_json.py | jq .

reviews-stats:
	@. .venv/bin/activate && ./.venv/bin/python scripts/reviews_stats.py | jq .

# Mini-Self-play: 3 Durchläufe, Reviews loggen
phase3-mini: self-play reviews-dump reviews-stats
self-play:
	@API=$(API) KEY=$(KEY) ROUNDS=$(ROUNDS) ./.venv/bin/python scripts/self_play.py | jq .

# Graph aus Learned-Daten + Stats
graph-from-learn:
	@. .venv/bin/activate && ./scripts/graph_from_learned.py | jq .
graph-stats:
	@. .venv/bin/activate && curl -s $(API)/graph/stats | jq .
phase2-graph:
	@$(MAKE) graph-from-learn && $(MAKE) graph-stats

# Learn-Endpoints (HTTP)
learn-scan-http:
	@curl -s -X POST "$(API)/learn/scan" | jq .
learn-stats-http:
	@curl -s "$(API)/learn/stats" | jq .

# LLM – pings & smoke (nur sinnvoll, wenn ollama & Modelle vorhanden)
llm-ping:
	@. .venv/bin/activate && ./.venv/bin/python scripts/llm_ping.py

llm-enhance-smoke:
	@. .venv/bin/activate && LLM_PROVIDER=ollama LLM_MODEL=mistral USE_LLM_ENHANCE=1 ./.venv/bin/python scripts/llm_enhance_smoke.py | jq .

phase3-autotune:
	@. .venv/bin/activate && API=$(API) KEY=$(KEY) PASSES=$(PASSES) ./.venv/bin/python scripts/phase3_autotune_call.py

# (optional) Modelle ziehen
ollama-pull-basic:
	@ollama pull mistral || true
	@ollama pull llama3:8b || true
	@ollama pull phi3 || true

ollama-pull-creative:
	@ollama pull mixtral:8x7b || true
