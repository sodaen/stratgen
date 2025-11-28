#!/usr/bin/env python
import sys, os
sys.path.insert(0, os.getcwd())
import json, sqlite3, sys
from pathlib import Path
from services.graph_extract import extract_nodes_and_edges
from services.knowledge_graph import upsert_nodes, upsert_edges

DB = Path("data/projects.sqlite")

def main(limit: int | None = None):
    if not DB.exists():
        print("no DB at", DB, file=sys.stderr)
        return
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        sql = "SELECT source_id, features_json FROM learned_patterns ORDER BY id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = cur.execute(sql).fetchall()
    total_nodes, total_edges = 0, 0
    for sid, feats_json in rows:
        try:
            feats = json.loads(feats_json)
            nodes, edges = extract_nodes_and_edges(feats)
            total_nodes += upsert_nodes(nodes)
            total_edges += upsert_edges(edges)
        except Exception as e:
            print("[WARN]", sid, e, file=sys.stderr)
    print(json.dumps({"ok": True, "nodes_added": total_nodes, "edges_added": total_edges}, ensure_ascii=False))

if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(lim)