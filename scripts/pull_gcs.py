import os
from google.cloud import storage
 
bucket_name = os.environ["GCS_BUCKET"]
object_path = os.environ.get("GCS_OBJECT_PATH", "").strip().strip("/")
artifacts   = os.environ["ARTIFACTS_DIR"]
 
if not bucket_name:
    raise ValueError("GCS_BUCKET is empty — check the Jenkins credential 'gcs-bucket-name'")
 
client = storage.Client()
bucket = client.bucket(bucket_name)
 
# ── Resolve object path ───────────────────────────────────────────────────────
if not object_path:
    print("GCS_OBJECT_PATH not set — fetching the most recently uploaded file...")
    blobs = sorted(
        client.list_blobs(bucket_name),
        key=lambda b: b.updated,
        reverse=True,
    )
    if not blobs:
        raise RuntimeError(f"Bucket '{bucket_name}' is empty — nothing to download")
    latest = blobs[0]
    object_path = latest.name
    print(f"Latest file: {object_path} (uploaded {latest.updated})")
 
filename = os.path.basename(object_path)
if not filename:
    raise ValueError(f"Could not derive filename from GCS_OBJECT_PATH='{object_path}'")
 
# ── Download ──────────────────────────────────────────────────────────────────
blob = bucket.blob(object_path)
dest = os.path.join(artifacts, filename)
 
print(f"Downloading gs://{bucket_name}/{object_path} -> {dest}")
blob.download_to_filename(dest)
print(f"Done: {filename} ({os.path.getsize(dest):,} bytes)")
 
with open(os.path.join(artifacts, ".downloaded_file"), "w") as f:
    f.write(filename)

