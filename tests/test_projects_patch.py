import json
from fastapi.testclient import TestClient
from backend.api import app

def test_patch_project_updates_outline_and_style():
    c = TestClient(app)
    # create
    r = c.post("/projects/save", headers={"X-API-Key":"dev"}, json={
        "customer_name":"T",
        "topic":"X",
        "outline":{"title":"T0","sections":[]}
    })
    assert r.status_code == 200
    pid = r.json()["project"]["id"]

    # patch outline as json string + style as name
    r = c.patch(f"/projects/{pid}", headers={"X-API-Key":"dev"}, json={
        "outline": json.dumps({"title":"T1","sections":[{"title":"One"}]}),
        "style": "minimal"
    })
    assert r.status_code == 200, r.text
    pj = r.json()["project"]
    assert pj["outline"]["title"] == "T1"
    assert pj["style"] == "minimal"

    # preview must still work
    r = c.post(f"/projects/{pid}/preview", headers={"X-API-Key":"dev"}, json={"style":"minimal","width":640,"height":360})
    assert r.status_code == 200

    # export too
    r = c.post(f"/projects/{pid}/export", headers={"X-API-Key":"dev"}, json={"style":"minimal","filename":"x.pptx"})
    assert r.status_code == 200
