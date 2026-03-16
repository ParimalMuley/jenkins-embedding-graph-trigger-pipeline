import os
import json
import sys
 
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
 
artifacts  = os.environ["ARTIFACTS_DIR"]
neo4j_uri  = os.environ["NEO4J_URI"]
qdrant_url = os.environ["QDRANT_HOST"]
collection = os.environ["QDRANT_COLLECTION"]
 

driver = GraphDatabase.driver(neo4j_uri, auth=None)
with driver.session() as s:
    node_count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    rel_count  = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
driver.close()
 

qclient    = QdrantClient(url=qdrant_url)
vec_count  = qclient.get_collection(collection).vectors_count
 

print(f"Neo4j  -> nodes: {node_count:,}  |  relationships: {rel_count:,}")
print(f"Qdrant -> collection: '{collection}'  |  vectors: {vec_count:,}")
 
report = {
    "neo4j":  {"nodes": node_count, "relationships": rel_count},
    "qdrant": {"collection": collection, "vectors": vec_count},
}
with open(os.path.join(artifacts, "pipeline_report.json"), "w") as fh:
    json.dump(report, fh, indent=2)
 
if node_count == 0 or vec_count == 0:
    print("ERROR: One or more stores contain zero records — failing build.")
    sys.exit(1)
 
print("Verification passed.")
