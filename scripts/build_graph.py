import os
import json
import time
 
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt
 
artifacts = os.environ["ARTIFACTS_DIR"]
api_key   = os.environ["GROQ_API_KEY"]
base_url  = os.environ["GROQ_BASE_URL"]
llm_model = os.environ["LLM_MODEL"]   # llama-3.3-70b-versatile
 
# Groq exposes an OpenAI-compatible endpoint — no extra SDK needed
client = OpenAI(api_key=api_key, base_url=base_url)
 
SYSTEM_PROMPT = """\
You are a knowledge-graph extraction engine.
Given a text passage, extract ALL entities and the relationships between them.
 
Return ONLY a valid JSON object (no markdown, no commentary) matching this schema:
{
  "entities": [
    {
      "id":         "<unique_snake_case_within_this_passage>",
      "label":      "<EntityType>",
      "name":       "<display name>",
      "properties": {"key": "value"}
    }
  ],
  "relationships": [
    {
      "source":     "<entity_id>",
      "target":     "<entity_id>",
      "type":       "<RELATIONSHIP_TYPE>",
      "properties": {"key": "value"}
    }
  ]
}
 
Common entity labels    : Person, Organization, Location, Concept, Event, Product, Date
Common relationship types: WORKS_FOR, LOCATED_IN, MENTIONS, RELATED_TO, PART_OF, CREATED_BY
"""
 
with open(os.path.join(artifacts, "chunks_with_embeddings.json")) as fh:
    chunks = json.load(fh)
 
@retry(wait=wait_exponential(multiplier=1, min=2, max=60),
       stop=stop_after_attempt(5))
def extract_graph(text: str) -> dict:
    resp = client.chat.completions.create(
        model=llm_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Text:\n\n{text[:4000]}"},
        ],
    )
    return json.loads(resp.choices[0].message.content)
 
all_entities: dict[str, dict] = {}
all_relationships: list[dict] = []
 
for i, chunk in enumerate(chunks):
    print(f"  [{i+1}/{len(chunks)}] Extracting from {chunk['chunk_id']} ...")
    try:
        result = extract_graph(chunk["text"])
 
        for ent in result.get("entities", []):
            uid = f"{chunk['chunk_id']}_{ent['id']}"
            all_entities[uid] = {
                **ent,
                "global_id":  uid,
                "chunk_id":   chunk["chunk_id"],
                "source_doc": chunk["source"],
            }
 
        for rel in result.get("relationships", []):
            all_relationships.append({
                **rel,
                "source_global": f"{chunk['chunk_id']}_{rel['source']}",
                "target_global": f"{chunk['chunk_id']}_{rel['target']}",
                "chunk_id":      chunk["chunk_id"],
            })
 
    except Exception as exc:
        print(f"  WARNING: chunk {i} skipped — {exc}")
 
    # Groq free tier: 6,000 tokens/min — pace to avoid 429s
    time.sleep(1)
 
graph = {
    "entities":      list(all_entities.values()),
    "relationships": all_relationships,
}
 
out_path = os.path.join(artifacts, "knowledge_graph.json")
with open(out_path, "w") as fh:
    json.dump(graph, fh, indent=2)
 
print(
    f"Graph complete: {len(graph['entities'])} entities, "
    f"{len(graph['relationships'])} relationships -> {out_path}"
)
