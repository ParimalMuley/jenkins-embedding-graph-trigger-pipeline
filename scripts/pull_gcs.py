import os
from google.cloud import storage
 
bucket_name = os.environ["GCS_BUCKET"]
object_path = os.environ["GCS_OBJECT_PATH"]
artifacts   = os.environ["ARTIFACTS_DIR"]
 
# google-cloud-storage picks up credentials automatically from the
# GCE metadata server when running on a GCP VM.
client   = storage.Client()
blob     = client.bucket(bucket_name).blob(object_path)
filename = os.path.basename(object_path)
dest     = os.path.join(artifacts, filename)
 
print(f"Downloading gs://{bucket_name}/{object_path} -> {dest}")
blob.download_to_filename(dest)
print(f"Done: {filename} ({os.path.getsize(dest):,} bytes)")
 
with open(os.path.join(artifacts, ".downloaded_file"), "w") as f:
    f.write(filename)
