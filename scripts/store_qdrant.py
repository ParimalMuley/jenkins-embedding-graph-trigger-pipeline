import os
import json
import uuid
 
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    UpdateStatus,
)
 
artifacts  = os.environ["ARTIFACTS_DIR"]
host       = os.environ["QDRANT_HOST"]
collection = os.environ["QDRANT_COLLECTION"]
dim        = int(os.environ["EMBEDDING_DIMENSION"])
 
with open(os.path.join(artifacts, "chunks_with_embeddings.json")) as fh:
    chunks = json.load(fh)
 
client = QdrantClient(url=host)
 

existing = [c.name for c in client.get_collections().collections]
if collection not in existing:
    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    print(f"Created collection '{collection}' (dim={dim})")
else:
    print(f"Collection '{collection}' already exists — upserting points")
 

points = [
    PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])),
        vector=c["embedding"],
        payload={
            "chunk_id":     c["chunk_id"],
            "source":       c["source"],
            "chunk_idx":    c["chunk_idx"],
            "total_chunks": c["total_chunks"],
            "text":         c["text"],
        },
    )
    for c in chunks
]
 

BATCH  = 64
total  = len(points)
n_batches = -(-total // BATCH)
 
print(f"Upserting {total} vectors in {n_batches} batches ...")
for i in range(0, total, BATCH):
    result = client.upsert(
        collection_name=collection,
        points=points[i : i + BATCH],
    )
    if result.status != UpdateStatus.COMPLETED:
        raise RuntimeError(f"Qdrant upsert failed at batch {i // BATCH}: {result}")
    print(f"  Batch {i // BATCH + 1}/{n_batches} done")
 
print(f"Qdrant load complete: {total} vectors in '{collection}'.")
