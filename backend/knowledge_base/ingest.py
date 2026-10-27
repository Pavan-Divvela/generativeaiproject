import json
import re
from pathlib import Path
from config import Config

def parse_markdown_to_chunks(file_path: Path):
    """
    Parses a markdown document into distinct chunks based on headers.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc_name = file_path.stem
    sections = re.split(r'\n(?=#{1,3}\s+)', content)
    chunks = []

    for idx, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue
        
        # Extract title from first line
        lines = sec.split("\n")
        title = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else title

        chunk_id = f"{doc_name}_{idx+1}"
        chunks.append({
            "id": chunk_id,
            "document": doc_name,
            "title": title,
            "content": sec,
            "body": body
        })

    return chunks

def ingest_all_documents():
    """Reads all markdown documents, chunks them, and saves to chunks.json."""
    Config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    doc_files = list(Config.DOCUMENTS_DIR.glob("*.md"))

    for doc_file in doc_files:
        chunks = parse_markdown_to_chunks(doc_file)
        all_chunks.extend(chunks)

    with open(Config.CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"Successfully ingested {len(all_chunks)} chunks from {len(doc_files)} documents into {Config.CHUNKS_FILE}")
    return all_chunks

if __name__ == "__main__":
    ingest_all_documents()
