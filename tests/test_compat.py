from services.compat import ensure_outline_dict, resolve_style
from services.style_presets import get_style_options

def test_ensure_outline_dict_accepts_dict():
    d = {"title":"Demo","sections":[]}
    assert ensure_outline_dict(d) is d

def test_ensure_outline_dict_accepts_json_str():
    s = '{"title":"Demo","sections":[{"title":"One"}]}'
    out = ensure_outline_dict(s)
    assert isinstance(out, dict)
    assert out.get("title") == "Demo"
    assert out.get("sections")[0]["title"] == "One"

def test_ensure_outline_dict_on_garbage():
    out = ensure_outline_dict("not json at all")
    assert out == {}

def test_resolve_style_known_brand():
    style = resolve_style("brand")
    assert isinstance(style, dict)
    # muss mind. diese Schlüssel haben
    for k in ("title_font","body_font","accent_color","text_color","bg_color"):
        assert k in style

def test_resolve_style_dict_passthrough():
    raw = {"title_font":"X","body_font":"Y","accent_color":"AA0000","text_color":"111111","bg_color":"FFFFFF"}
    style = resolve_style(raw)
    assert style is raw

def test_resolve_style_unknown_falls_back():
    style = resolve_style("does-not-exist")
    assert isinstance(style, dict)
    # Fallback liefert mind. diese Keys
    for k in ("title_font","body_font","accent_color","text_color","bg_color"):
        assert k in style
