from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import hashlib

COLL = "strategies"
emb = SentenceTransformer("BAAI/bge-m3")  # gleiche Embeddings wie im Projekt
vec = emb.encode("seed", normalize_embeddings=True).tolist()
dim = len(vec)

q = QdrantClient(host="localhost", port=6333)
try:
    q.get_collection(COLL)
    print("Collection existiert bereits.")
except Exception:
    print(f"Erzeuge Collection '{COLL}' (dim={dim}) …")
    q.recreate_collection(collection_name=COLL, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

q.upsert(collection_name=COLL, points=[{
    "id": hashlib.md5(b"seed").hexdigest(),
    "vector": vec,
    "payload": {"text": "Seed"}
}])
print("OK: Seedpunkt geschrieben.")
