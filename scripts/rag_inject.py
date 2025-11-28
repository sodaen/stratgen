
import sys, json, requests, os

API = os.environ.get("API","http://127.0.0.1:8001")
KEY = os.environ.get("KEY","dev")
HEAD = {"X-API-Key": KEY}

def get(pid):
    return requests.get(f"{API}/projects/{pid}", headers=HEAD).json()

def save(doc):
    return requests.post(f"{API}/projects/save", headers=HEAD, json=doc).json()

def search(q, k=8, semantic=True):
    sem = 1 if semantic else 0
    r = requests.get(f"{API}/knowledge/search",
                     params={"q":q,"limit":k,"semantic":sem})
    r.raise_for_status()
    return r.json().get("results",[])

def main():
    if len(sys.argv)<3:
        print("Usage: rag_inject.py <PROJECT_ID> <QUERY> [K=8]")
        sys.exit(1)
    pid  = sys.argv[1]
    q    = sys.argv[2]
    k    = int(sys.argv[3]) if len(sys.argv)>3 else 8

    proj = get(pid)
    res  = search(q, k=k, semantic=True)
    ctx  = "\n\n".join([r.get("snippet") or r.get("text","") for r in res])

    # Kontext in das Projekt-Dokument anhängen (z.B. unter 'notes' oder 'brief')
    doc = proj
    base = (doc.get("brief") or "") + "\n\n---\n# Wissenskontext (Top-{}):\n{}\n".format(k, ctx)
    doc["brief"] = base
    out = save(doc)
    print(json.dumps({"ok":True,"project_id":pid,"added_snippets":len(res)}, ensure_ascii=False))
if __name__ == "__main__":
    main()
