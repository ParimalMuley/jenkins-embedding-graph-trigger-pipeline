import os
import json
 
from neo4j import GraphDatabase
 
artifacts = os.environ["ARTIFACTS_DIR"]
uri       = os.environ["NEO4J_URI"]
 
with open(os.path.join(artifacts, "knowledge_graph.json")) as fh:
    graph = json.load(fh)
 
driver = GraphDatabase.driver(uri, auth=None)
 
 
def safe_label(raw: str) -> str:
    """Strip characters that are illegal in Cypher labels."""
    return "".join(c for c in raw if c.isalnum() or c == "_") or "Entity"
 
def safe_rel_type(raw: str) -> str:
    return "".join(c for c in raw.upper() if c.isalnum() or c == "_") or "RELATED_TO"
 
def upsert_entities(tx, batch: list[dict]) -> None:
    for ent in batch:
        label = safe_label(ent.get("label", "Entity"))
        props = {
            "global_id":  ent["global_id"],
            "name":       ent.get("name", ""),
            "chunk_id":   ent.get("chunk_id", ""),
            "source_doc": ent.get("source_doc", ""),
            **{k: str(v) for k, v in ent.get("properties", {}).items()},
        }
        tx.run(
            f"MERGE (n:{label} {{global_id: $gid}}) SET n += $props",
            gid=ent["global_id"],
            props=props,
        )
 
def upsert_relationships(tx, batch: list[dict]) -> None:
    for rel in batch:
        rtype = safe_rel_type(rel.get("type", "RELATED_TO"))
        tx.run(
            f"""
            MATCH (a {{global_id: $src}})
            MATCH (b {{global_id: $tgt}})
            MERGE (a)-[r:{rtype}]->(b)
            SET r += $props
            """,
            src=rel["source_global"],
            tgt=rel["target_global"],
            props={k: str(v) for k, v in rel.get("properties", {}).items()},
        )
 
BATCH = 100
entities = graph["entities"]
rels     = graph["relationships"]
 
print(f"Upserting {len(entities)} nodes ...")
with driver.session() as session:
    for i in range(0, len(entities), BATCH):
        session.execute_write(upsert_entities, entities[i : i + BATCH])
        print(f"  Nodes batch {i // BATCH + 1} done")
 
print(f"Upserting {len(rels)} relationships ...")
with driver.session() as session:
    for i in range(0, len(rels), BATCH):
        session.execute_write(upsert_relationships, rels[i : i + BATCH])
        print(f"  Relationships batch {i // BATCH + 1} done")
 
driver.close()
print("Neo4j load complete.")
