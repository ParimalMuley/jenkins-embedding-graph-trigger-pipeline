import os
import json
import pathlib

from langchain_text_splitters import RecursiveCharacterTextSplitter

artifacts     = os.environ["ARTIFACTS_DIR"]
filename      = os.environ["DOWNLOADED_FILE"]
filepath      = os.path.join(artifacts, filename)
chunk_size    = int(os.environ["CHUNK_SIZE"])
chunk_overlap = int(os.environ["CHUNK_OVERLAP"])

ext = pathlib.Path(filename).suffix.lower()


if ext == ".pdf":
    from pypdf import PdfReader
    reader   = PdfReader(filepath)
    raw_text = "\n\n".join(p.extract_text() or "" for p in reader.pages)

elif ext in (".docx", ".doc"):
    from docx import Document
    doc      = Document(filepath)
    raw_text = "\n\n".join(p.text for p in doc.paragraphs)

else:
    with open(filepath, "r", errors="replace") as fh:
        raw_text = fh.read()

print(f"Extracted {len(raw_text):,} characters from {filename}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    length_function=len,
)
docs = splitter.create_documents([raw_text])

chunks = [
    {
        "chunk_id":     f"{filename}_chunk_{i:04d}",
        "source":       filename,
        "chunk_idx":    i,
        "total_chunks": len(docs),
        "text":         doc.page_content,
    }
    for i, doc in enumerate(docs)
]

out_path = os.path.join(artifacts, "chunks.json")
with open(out_path, "w") as fh:
    json.dump(chunks, fh, indent=2)

print(f"Produced {len(chunks)} chunks -> {out_path}")
