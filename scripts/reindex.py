#!/usr/bin/env python3
from services.ingest import reindex
import argparse, json
p = argparse.ArgumentParser()
p.add_argument("--recreate", action="store_true")
args = p.parse_args()
print(json.dumps(reindex(recreate=args.recreate), ensure_ascii=False, indent=2))
