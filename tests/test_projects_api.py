from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)

def test_projects_preview_and_export_roundtrip():
    # 1) Projekt speichern
    r = client.post("/projects/save",
        headers={"X-API-Key":"dev"},
        json={
            "customer_name":"Acme GmbH",
            "topic":"Demo",
            "outline":{
                "title":"Demo", "subtitle":"Kurz",
                "sections":[{"title":"One","bullets":["A","B"]}]
            }
        }
    )
    assert r.status_code == 200, r.text
    pid = r.json()["project"]["id"]
    assert pid

    # 2) Preview: sollte image/png liefern
    r2 = client.post(f"/projects/{pid}/preview",
        headers={"X-API-Key":"dev"},
        json={"style":"brand","width":800,"height":450}
    )
    assert r2.status_code == 200, r2.text
    ct = r2.headers.get("content-type","")
    assert ct.startswith("image/png")

    # 3) Export: sollte PPTX liefern
    r3 = client.post(f"/projects/{pid}/export",
        headers={"X-API-Key":"dev"},
        json={"style":"brand","filename":"proj_export.pptx"}
    )
    assert r3.status_code == 200, r3.text
    ct3 = r3.headers.get("content-type","")
    assert ct3.startswith("application/vnd.openxmlformats-officedocument.presentationml.presentation")
    # Inhalt ist eine ZIP-basierte PPTX (PK Header)
    body = r3.content
    assert body[:2] == b"PK"
