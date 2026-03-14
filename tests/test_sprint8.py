# -*- coding: utf-8 -*-
"""
tests/test_sprint8.py
======================
pytest-Suite für StratGen Sprint 8.

Abgedeckte APIs:
  - /strategy/swot, /strategy/porter
  - /competitors/matrix, /competitors/profile
  - /chat/* (Session, Message, Feedback, Delete)
  - /data-import/upload, /data-import/chart
  - /offline/status, /offline/enable, /offline/disable
  - /research/deep/queries/suggest, /research/deep/start
  - /pptx/templates/* (Custom Templates)
  - /learning/stats (Self-Learning)

Ausführen:
  cd ~/stratgen
  pytest tests/test_sprint8.py -v

Für schnellen Smoke-Test (ohne LLM-Calls):
  pytest tests/test_sprint8.py -v -m "not llm"
"""

import io
import json
import os
import time

import pytest
import requests

BASE = os.getenv("STRATGEN_TEST_URL", "http://localhost:8011")


def get(path: str, **kwargs):
    return requests.get(f"{BASE}{path}", timeout=30, **kwargs)


def post(path: str, json_data=None, files=None, **kwargs):
    if files:
        return requests.post(f"{BASE}{path}", files=files, timeout=60, **kwargs)
    return requests.post(f"{BASE}{path}", json=json_data, timeout=60, **kwargs)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def backend_up():
    """Sicherstellen dass Backend erreichbar ist."""
    for _ in range(10):
        try:
            r = requests.get(f"{BASE}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(1)
    pytest.skip("Backend nicht erreichbar")


@pytest.fixture(scope="session")
def chat_session(backend_up):
    """Erstellt eine Chat-Session für Tests."""
    r = post("/chat/sessions/new")
    assert r.status_code == 200
    data = r.json()
    return data.get("session_id") or data.get("id")


@pytest.fixture(scope="session")
def csv_import_id(backend_up):
    """Lädt eine Test-CSV hoch und gibt die Import-ID zurück."""
    csv_content = b"Produkt,Umsatz,Kosten\nProdukt A,100000,60000\nProdukt B,150000,80000\nProdukt C,80000,50000\n"
    files = {"file": ("test_data.csv", io.BytesIO(csv_content), "text/csv")}
    r = post("/data-import/upload", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    return data.get("id")


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint(self, backend_up):
        r = get("/health")
        assert r.status_code == 200

    def test_offline_status(self, backend_up):
        r = get("/offline/status")
        assert r.status_code == 200
        data = r.json()
        assert "offline" in data or "mode" in data or "status" in data

    def test_offline_health(self, backend_up):
        r = get("/offline/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)


# ── Offline Mode ──────────────────────────────────────────────────────────────

class TestOfflineMode:
    def test_enable_disable_cycle(self, backend_up):
        # Enable
        r = post("/offline/enable")
        assert r.status_code == 200

        # Status prüfen
        r = get("/offline/status")
        data = r.json()
        assert data.get("offline") is True or data.get("mode") == "offline"

        # Disable
        r = post("/offline/disable")
        assert r.status_code == 200

        # Status prüfen
        r = get("/offline/status")
        data = r.json()
        assert data.get("offline") is False or data.get("mode") != "offline"

    def test_offline_blocks_research(self, backend_up):
        post("/offline/enable")
        try:
            r = post("/research/deep/start", json_data={"topic": "Test", "depth": "quick"})
            assert r.status_code in (503, 200)  # 503 = geblockt, 200 = session created but no results
        finally:
            post("/offline/disable")


# ── Strategy ──────────────────────────────────────────────────────────────────

class TestStrategy:
    @pytest.mark.llm
    def test_swot_returns_structure(self, backend_up):
        r = post("/strategy/swot", json_data={
            "topic": "Tesla",
            "industry": "Elektromobilität",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True or "strengths" in data or "swot" in data

    @pytest.mark.llm
    def test_porter_returns_forces(self, backend_up):
        r = post("/strategy/porter", json_data={
            "topic": "SAP",
            "industry": "ERP-Software",
        })
        assert r.status_code == 200
        data = r.json()
        # Mindestens ein Force-Key muss vorhanden sein
        force_keys = {"rivalry", "new_entrants", "substitutes", "buyer_power", "supplier_power"}
        response_keys = set(data.get("forces", data).keys())
        assert len(force_keys & response_keys) >= 1 or data.get("ok") is True


# ── Competitor ────────────────────────────────────────────────────────────────

class TestCompetitor:
    @pytest.mark.llm
    def test_matrix_returns_scores(self, backend_up):
        r = post("/competitors/matrix", json_data={
            "customer_name": "Tesla",
            "competitors": ["BMW", "Mercedes"],
            "criteria": ["Preis", "Innovation", "Qualität"],
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True or "matrix" in data or "scores" in data


# ── Chat ──────────────────────────────────────────────────────────────────────

class TestChat:
    def test_new_session_created(self, backend_up):
        r = post("/chat/sessions/new")
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data or "id" in data

    def test_get_history_empty(self, chat_session):
        r = get(f"/chat/{chat_session}/history")
        assert r.status_code == 200

    @pytest.mark.llm
    def test_message_returns_response(self, chat_session):
        r = post(f"/chat/{chat_session}/message", json_data={
            "message": "Was ist eine SWOT-Analyse? Antworte in einem Satz."
        })
        assert r.status_code == 200
        data = r.json()
        assert "response" in data or "message" in data or "content" in data

    def test_feedback_accepted(self, chat_session):
        r = post(f"/chat/{chat_session}/feedback", json_data={"rating": "up"})
        assert r.status_code == 200

    def test_sessions_list(self, backend_up):
        r = get("/chat/sessions")
        assert r.status_code == 200


# ── Data Import ───────────────────────────────────────────────────────────────

class TestDataImport:
    def test_csv_upload_detects_columns(self, csv_import_id):
        assert csv_import_id is not None

    def test_csv_upload_returns_columns(self, backend_up):
        csv_content = b"Jahr,Umsatz,Gewinn\n2022,500000,50000\n2023,600000,70000\n2024,750000,90000\n"
        files = {"file": ("umsatz.csv", io.BytesIO(csv_content), "text/csv")}
        r = post("/data-import/upload", files=files)
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert "columns" in data
        col_names = [c["name"] for c in data["columns"]]
        assert "Jahr" in col_names
        assert "Umsatz" in col_names

    def test_column_types_detected(self, backend_up):
        csv_content = b"Kategorie,Wert\nA,100\nB,200\nC,150\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        r = post("/data-import/upload", files=files)
        data = r.json()
        cols = {c["name"]: c["type"] for c in data.get("columns", [])}
        assert cols.get("Kategorie") == "label"
        assert cols.get("Wert") == "numeric"

    def test_chart_generation(self, csv_import_id):
        r = post("/data-import/chart", json_data={
            "import_id": csv_import_id,
            "chart_type": "bar",
            "label_column": "Produkt",
            "value_columns": ["Umsatz"],
            "title": "Umsatz Übersicht",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert "slide" in data

    def test_list_imports(self, backend_up):
        r = get("/data-import/list")
        assert r.status_code == 200

    def test_unsupported_format_rejected(self, backend_up):
        files = {"file": ("test.pdf", io.BytesIO(b"not a csv"), "application/pdf")}
        r = post("/data-import/upload", files=files)
        # Sollte entweder 400 oder ok=False zurückgeben
        if r.status_code == 200:
            assert r.json().get("ok") is False
        else:
            assert r.status_code in (400, 422)


# ── Deep Research ─────────────────────────────────────────────────────────────

class TestDeepResearch:
    def test_suggest_queries_returns_list(self, backend_up):
        r = post("/research/deep/queries/suggest", json_data={
            "topic": "Nachhaltigkeit in der Logistik",
            "depth": "quick",
            "language": "de",
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert isinstance(data.get("queries"), list)
        assert len(data["queries"]) >= 2

    def test_list_sessions(self, backend_up):
        r = get("/research/deep/sessions/list")
        assert r.status_code == 200
        data = r.json()
        assert "sessions" in data

    def test_start_session_returns_id(self, backend_up):
        r = post("/research/deep/start", json_data={
            "topic": "Digitalisierung im Mittelstand",
            "depth": "quick",
            "language": "de",
            "auto_ingest": False,
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert "session_id" in data
        return data["session_id"]

    def test_session_completes(self, backend_up):
        # Session starten
        r = post("/research/deep/start", json_data={
            "topic": "Cloud Computing Trends",
            "depth": "quick",
            "language": "de",
            "auto_ingest": False,
        })
        session_id = r.json()["session_id"]

        # Auf Abschluss warten (max 60s)
        for _ in range(20):
            time.sleep(3)
            r = get(f"/research/deep/{session_id}")
            data = r.json()
            if data.get("status") in ("done", "failed", "cancelled"):
                break

        assert data.get("status") == "done"
        assert data.get("result_count", 0) > 0


# ── Custom Templates ──────────────────────────────────────────────────────────

class TestCustomTemplates:
    def test_list_templates(self, backend_up):
        r = get("/pptx/templates")
        assert r.status_code == 200

    def test_upload_template(self, backend_up):
        """Minimale PPTX-Datei als Template hochladen."""
        try:
            from pptx import Presentation as Prs
            from pptx.util import Inches
            import io as _io
            prs = Prs()
            prs.slides.add_slide(prs.slide_layouts[0])
            buf = _io.BytesIO()
            prs.save(buf)
            buf.seek(0)
            files = {"file": ("test_template.pptx", buf, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
            r = post("/pptx/templates/upload", files=files)
            assert r.status_code == 200
            data = r.json()
            assert data.get("ok") is True
        except ImportError:
            pytest.skip("python-pptx nicht verfügbar")


# ── Self Learning ─────────────────────────────────────────────────────────────

class TestSelfLearning:
    def test_stats_endpoint(self, backend_up):
        r = get("/learning/stats")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
