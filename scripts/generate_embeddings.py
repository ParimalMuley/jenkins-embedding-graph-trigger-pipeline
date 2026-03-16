import os
import json
import time
 
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt
 
artifacts       = os.environ["ARTIFACTS_DIR"]
base_url        = os.environ["LITELLM_BASE_URL"]
api_key         = os.environ["LITELLM_API_KEY"]
embedding_model = os.environ["EMBEDDING_MODEL"]   # qwen-embedding
 
client = OpenAI(api_key=api_key, base_url=base_url)
 
with open(os.path.join(artifacts, "chunks.json")) as fh:
    chunks = json.load(fh)
 
@retry(wait=wait_exponential(multiplier=1, min=2, max=30),
       stop=stop_after_attempt(5))
def embed_batch(texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(
        model=embedding_model,
        input=texts,
        encoding_format="float",
    )
    # Sort by index to guarantee order matches input
    return [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
 
# Single pod behind LiteLLM — keep batches modest
BATCH      = 16
RATE_DELAY = 0.3
total      = len(chunks)
 
for i in range(0, total, BATCH):
    batch = chunks[i : i + BATCH]
    texts = [c["text"] for c in batch]
    vecs  = embed_batch(texts)
    for chunk, vec in zip(batch, vecs):
        chunk["embedding"] = vec
    print(f"  Embedded {min(i + BATCH, total)}/{total} chunks")
    if i + BATCH < total:
        time.sleep(RATE_DELAY)
 
out_path = os.path.join(artifacts, "chunks_with_embeddings.json")
with open(out_path, "w") as fh:
    json.dump(chunks, fh)
 
print(f"Saved {total} embeddings -> {out_path}")
