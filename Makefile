SHELL := /bin/bash
BASE  := http://127.0.0.1:8011

STRATGEN_UNIT := stratgen.service
OLLAMA_UNIT   := ollama.service

LOGS_DIR := logs
FRONT_DIR ?= frontend
FRONT_PORT ?= 4173
FRONT_LOG := $(LOGS_DIR)/frontend.log
FRONT_PID := $(LOGS_DIR)/frontend.pid

.PHONY: backend-up backend-status backend-logs backend-restart backend-down backend-flags backend-wait \
        frontend-up frontend-logs frontend-down

## ==== Backend ====
backend-up:
	@echo "==> Starting ollama (optional) & stratgen"
	-@sudo systemctl start $(OLLAMA_UNIT) 2>/dev/null || true
	@sudo systemctl restart $(STRATGEN_UNIT)
	@$(MAKE) backend-wait

backend-wait:
	@echo "==> Waiting for /health ..."
	@for i in {1..60}; do \
		if curl -fsS $(BASE)/health >/dev/null; then echo "health OK"; exit 0; fi; \
		sleep 1; \
	done; \
	echo "health FAIL" >&2; exit 1

backend-status:
	@systemctl status --no-pager $(STRATGEN_UNIT)

backend-logs:
	@journalctl -u $(STRATGEN_UNIT) -f -n 200 --no-pager

backend-restart:
	@sudo systemctl restart $(STRATGEN_UNIT)
	@$(MAKE) backend-wait

backend-down:
	@sudo systemctl stop $(STRATGEN_UNIT)

backend-flags:
	@echo "==> Backend flags (/ops/status)"
	@curl -fsS $(BASE)/ops/status | jq '{env:.env, llm:.llm, rag_k:.rag_k, features:.features}' || true

## ==== Frontend (ohne systemd) ====
frontend-up:
	@mkdir -p $(LOGS_DIR)
	@echo "==> Starting frontend on :$(FRONT_PORT) (logs: $(FRONT_LOG))"
	-@if [ -f $(FRONT_PID) ]; then kill $$(cat $(FRONT_PID)) 2>/dev/null || true; rm -f $(FRONT_PID); fi
	-@pkill -f "vite.*$(FRONT_DIR)" 2>/dev/null || true
	@nohup bash -lc 'cd $(FRONT_DIR) && (command -v pnpm >/dev/null && pnpm install || npm install) && (command -v pnpm >/dev/null && pnpm run dev || npm run dev) -- --host 0.0.0.0 --port $(FRONT_PORT)' > $(FRONT_LOG) 2>&1 & echo $$! > $(FRONT_PID)
	@echo "frontend started (PID $$(cat $(FRONT_PID)))"

frontend-logs:
	@[ -f $(FRONT_LOG) ] && tail -n 200 -f $(FRONT_LOG) || (echo "no frontend log yet: $(FRONT_LOG)"; exit 1)

frontend-down:
	@echo "==> Stopping frontend"
	-@if [ -f $(FRONT_PID) ]; then kill $$(cat $(FRONT_PID)) 2>/dev/null || true; rm -f $(FRONT_PID); fi
	-@pkill -f "vite.*$(FRONT_DIR)" 2>/dev/null || true
	@echo "frontend stopped"
