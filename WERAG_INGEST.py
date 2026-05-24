#!/usr/bin/env python3
"""
Recursive RAG Ingestion for V93000 Test Programs & Code Files
=============================================================

Automatically processes ALL files in nested folders with local models:
- SENSOR_IC test programs (.tf, .lim, .spec, .pin, .lvl, .tim, .vec)
- Code files (.c, .h, .cpp, .py, .js)
- Documentation (.md, .txt)

Usage:
    python3 rag_ingest_recursive.py /path/to/v93k/project/
    python3 rag_ingest_recursive.py ./SENSOR_IC/
"""

import os
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

# CHANGED — Only embedding model path (no LLM needed for ingestion)
# EMBED_MODEL_PATH = Path.home() / "hugging_face_rag/models/nomic-embed-text"

# ChromaDB settings
CHROMA_PATH = "./chroma_db_v93k"
COLLECTION_NAME = "v93k_test_programs"

# File types to process
SUPPORTED_TYPES = (
    ".c", ".h", ".cpp", ".ino",           # Code files
    ".md", ".txt",                        # Documentation
    ".py", ".js", ".java",                # Additional languages
    ".xml", ".json",                      # Config files
    # ADDED — V93000 SmarTest file types
    ".tf", ".lim", ".spec", ".pin",       # V93K structured syntax
    ".lvl", ".tim", ".vec",               # V93K data/config files
)

# Folders to skip
SKIP_FOLDERS = {
    '.git', '__pycache__', 'node_modules', 
    '.venv', 'venv', '.DS_Store', '.pytest_cache'
}

# V93K-specific settings
CHUNK_SIZE = 256        # Smaller for dense V93K configs
CHUNK_OVERLAP = 50      # 20% overlap


# ════════════════════════════════════════════════════════════════════════════
# SETUP EMBEDDINGS
# ════════════════════════════════════════════════════════════════════════════

print("⚙️  Setting up embeddings...")

# REMOVED — LLM setup (not needed for ingestion)
# print(f"  Loading LLM: {MODEL_PATH}...")
# llm = Llama(...)

# CHANGED — Load only embedding model
print(f"  Loading embeddings: nomic-embed-text...")
embed_model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5")
print("  ✓ Embedding model loaded")
print("✓ Ready for ingestion\n")


# ════════════════════════════════════════════════════════════════════════════
# SETUP VECTOR DATABASE
# ════════════════════════════════════════════════════════════════════════════

print(f"📦 Setting up vector database at: {CHROMA_PATH}")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
chroma_collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

print(f"✓ Vector database ready (collection: {COLLECTION_NAME})\n")


# ════════════════════════════════════════════════════════════════════════════
# RECURSIVE FILE FINDER
# ════════════════════════════════════════════════════════════════════════════

def find_all_files(directory, supported_types, skip_folders):
    """
    Recursively find all supported files in directory and subdirectories
    """
    found_files = []
    
    for root, dirs, files in os.walk(directory):
        # Remove skip folders from dirs (prevents os.walk from descending)
        dirs[:] = [d for d in dirs if d not in skip_folders]
        
        # Find matching files in this directory
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in supported_types:
                file_path = os.path.join(root, filename)
                found_files.append(file_path)
    
    return sorted(found_files)


# ════════════════════════════════════════════════════════════════════════════
# CHUNK TEXT INTO SEGMENTS
# ════════════════════════════════════════════════════════════════════════════

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into overlapping chunks (token-aware for V93K files)
    """
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


# ════════════════════════════════════════════════════════════════════════════
# INGEST FILE
# ════════════════════════════════════════════════════════════════════════════

def ingest_file(file_path):
    """
    Read a file, chunk it, embed it, and store in vector database
    """
    
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Get relative path for better context
    rel_path = os.path.relpath(file_path)
    
    print(f"   📄 {rel_path}")
    print(f"      Size: {file_size:,} bytes | Type: {file_ext}")
    
    try:
        # Read file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        
        # Skip empty files
        if not text.strip():
            print(f"      ⏭️  Empty file, skipping")
            return False
        
        print(f"      Content: {len(text):,} characters")
        
        # Chunk the text
        chunks = chunk_text(text)
        print(f"      Chunks: {len(chunks)}")
        
        # Embed and store each chunk
        print(f"      ⏳ Embedding and storing...")
        
        for chunk_idx, chunk in enumerate(chunks):
            # Generate embedding
            embedding = embed_model.encode([chunk])[0].tolist()
            
            # Store in ChromaDB
            chroma_collection.add(
                ids=[f"{file_path}_chunk_{chunk_idx}"],
                embeddings=[embedding],
                metadatas=[{
                    "filename": file_name,
                    "source": file_path,
                    "rel_path": rel_path,
                    "type": "code" if file_ext in [".c", ".h", ".cpp", ".ino", ".py", ".js", ".tf", ".spec", ".lim"] else "text",
                    "file_ext": file_ext,
                    "chunk_idx": chunk_idx,
                    "total_chunks": len(chunks),
                }],
                documents=[chunk]
            )
        
        print(f"      ✅ Stored {len(chunks)} chunks!")
        return True
    
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    """
    Main entry point: recursively ingest all supported files
    """
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 rag_ingest_recursive.py <folder>")
        print("\nExamples:")
        print("  python3 rag_ingest_recursive.py ~/hugging_face_rag/v93k_projects/SENSOR_IC/")
        print("  python3 rag_ingest_recursive.py ./my_v93k_program/")
        print(f"\nSupported types: {', '.join(SUPPORTED_TYPES)}")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # Expand ~ if present
    target = os.path.expanduser(target)
    
    if not os.path.isdir(target):
        print(f"❌ Not a directory: {target}")
        sys.exit(1)
    
    print(f"📁 Scanning: {target}")
    print(f"   (recursively searching all subfolders)")
    print("-" * 70)
    
    # Find all files recursively
    files = find_all_files(target, SUPPORTED_TYPES, SKIP_FOLDERS)
    
    if not files:
        print(f"❌ No supported files found in {target}")
        print(f"Supported types: {', '.join(SUPPORTED_TYPES)}")
        sys.exit(1)
    
    print(f"\n📊 Found {len(files)} file(s) to process:\n")
    
    # Ingest files
    successful = 0
    failed = 0
    total_chunks = 0
    
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}]")
        if ingest_file(file_path):
            successful += 1
            total_chunks = chroma_collection.count()
        else:
            failed += 1
        print()
    
    # Summary
    final_chunks = chroma_collection.count()
    print("=" * 70)
    print(f"✅ DONE!")
    print(f"   Files processed:  {successful}")
    print(f"   Files failed:     {failed}")
    print(f"   Total chunks:     {final_chunks}")
    print(f"   Database:         {CHROMA_PATH}")
    print(f"   Collection:       {COLLECTION_NAME}")
    print("=" * 70)


if __name__ == "__main__":
    main()