def test_import_app():
    import importlib, os, sys
    sys.path.insert(0, os.getcwd())
    app = importlib.import_module("backend.api").app
    assert app is not None

def test_build_deck(tmp_path):
    import os
    from services.deck_filler import build_deck
    project = {
        "style":"brand","logo":"data/assets/logo.png",
        "outline":{"title":"Testdeck","sections":[{"title":"A","bullets":["x","y"]}]}
    }
    out = tmp_path/"smoke.pptx"
    p = build_deck(project, None, str(out), template="base")
    assert out.exists()

