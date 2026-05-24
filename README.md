# V93K RAG Assistant

A local, offline AI assistant for Advantest V93000 SmarTest 7 test program development.
Built on Qwen3.5-9B Q4, ChromaDB, and FastAPI — runs entirely on your machine with no cloud dependency.

---

## What It Does

Query your V93000 test program files in plain English. Ask about test methods, limits, timing, pin groups, or bin assignments. Request changes across multiple interconnected files. The assistant understands the full dependency chain between `.tf`, `.lim`, `.spec`, `.pin`, `.lvl`, `.tim`, `.vec`, and `.cpp` files and keeps changes consistent across all of them.

**Example queries:**

```
"What does ts_continuity do and what are its limits?"
"Add a new self-test for the X axis similar to ts_selftest_z"
"Review ts_scan_full for cross-file issues"
"Show me everything about the IDDQ test"
"What levelset does ts_idd_active use and what are the VDD voltages?"
```

---

## Project Structure

```
project/
│
├── WEBRAG_simple.py        ← web server — FastAPI + RAG + LLM inference
├── WEBRAG_simple.html      ← chat UI — served at http://ai.local:8000
├── WERAG_INGEST.py         ← ingestion script — reads files, embeds, stores in ChromaDB
│
├── v93k_dummy/             ← KNOWLEDGE FOLDER — your test program files
│   ├── pinconfig/
│   │   └── SENSOR_IC.pin
│   ├── levels/
│   │   └── SENSOR_IC.lvl
│   ├── timing/
│   │   └── SENSOR_IC.tim
│   ├── spec/
│   │   └── SENSOR_IC.spec
│   ├── limits/
│   │   └── SENSOR_IC.lim
│   ├── vectors/
│   │   └── SENSOR_IC_vectors.vec
│   ├── testmethods/
│   │   └── SENSOR_IC_testmethods.cpp
│   ├── testflow/
│   │   └── SENSOR_IC.tf
│   └── docs/
│       └── SENSOR_IC_KNOWLEDGE_BASE.md
│
└── chroma_db_v93k/         ← RAG FOLDER — ChromaDB vector database (auto-created)
```

> **v93k_dummy/** is the knowledge folder. Put all your test program files here before ingesting.
> **chroma_db_v93k/** is created automatically by the ingestion script. Do not edit manually.

---

## Requirements

### Hardware

| Component | Minimum | Recommended |
|---|---|---|
| GPU VRAM | 6 GB | 8 GB |
| System RAM | 8 GB | 16 GB |
| Storage | 10 GB free | 20 GB free |

Tested on: Ubuntu 24, NVIDIA RTX 3070 8GB, AMD Ryzen 7 5800X.

### Python version

Python 3.10 or later.

### Python libraries

Install all dependencies with:

```bash
pip install llama-cpp-python \
            fastapi \
            uvicorn \
            pydantic \
            chromadb \
            sentence-transformers \
            --break-system-packages
```

| Library | Purpose |
|---|---|
| `llama-cpp-python` | Runs the GGUF quantized LLM locally on GPU |
| `fastapi` | Web server framework — handles HTTP routes |
| `uvicorn` | ASGI server — runs FastAPI |
| `pydantic` | Request/response validation |
| `chromadb` | Vector database — stores and retrieves embedded chunks |
| `sentence-transformers` | Embedding model — converts text to vectors for RAG |

### Model files

Download the LLM and embedding model to your local model folder:

```bash
# LLM — Qwen3.5-9B Q4 (primary inference model)
# ~6GB download
python3 model_download_qwen3p5reasoning.py

# Embedding model — downloaded automatically on first run
# nomic-ai/nomic-embed-text-v1.5 (~270MB, cached by sentence-transformers)
```

---

## Step 1 — Ingest Your Knowledge Base

Run the ingestion script pointing it at your knowledge folder. This reads all supported files, splits them into chunks, embeds each chunk, and stores them in ChromaDB.

```bash
python3 WERAG_INGEST.py ./v93k_dummy/
```

You will see output like:

```
⚙️  Setting up embeddings...
  Loading embeddings: nomic-embed-text...
  ✓ Embedding model loaded
✓ Ready for ingestion

📦 Setting up vector database at: ./chroma_db_v93k
✓ Vector database ready (collection: v93k_test_programs)

📁 Scanning: ./v93k_dummy/
──────────────────────────────────────────────────────────────────────

📊 Found 8 file(s) to process:

[1/8]
   📄 v93k_dummy/testflow/SENSOR_IC.tf
      Size: 14,832 bytes | Type: .tf
      Content: 12,441 characters
      Chunks: 49
      ⏳ Embedding and storing...
      ✅ Stored 49 chunks!
...

══════════════════════════════════════════════════════════════════════
✅ DONE!
   Files processed:  8
   Files failed:     0
   Total chunks:     312
   Database:         ./chroma_db_v93k
   Collection:       v93k_test_programs
══════════════════════════════════════════════════════════════════════
```

**Supported file types ingested automatically:**

`.tf` `.lim` `.spec` `.pin` `.lvl` `.tim` `.vec` `.cpp` `.c` `.h` `.md` `.txt` `.py` `.js` `.json` `.xml`

**Re-ingesting after changes:**

If you modify files in `v93k_dummy/`, delete the ChromaDB folder and re-run ingestion:

```bash
rm -rf chroma_db_v93k/
python3 WERAG_INGEST.py ./v93k_dummy/
```

---

## Step 2 — Start the Web Server

```bash
python3 WEBRAG_simple.py
```

You will see:

```
Loading model from /home/alex/hugging_face_rag/models/qwen3.5-9b-q4/Qwen_Qwen3.5-9B-Q4_K_M.gguf...
llama_context: n_ctx_seq (16384) < n_ctx_train (262144) -- the full capacity of the model will not be utilized
Model loaded.

⚙️  Setting up ChromaDB RAG...
  Loading embeddings: nomic-ai/nomic-embed-text-v1.5...
  ✓ Embedding model loaded
  Connecting to ChromaDB: ./chroma_db_v93k
  ✓ ChromaDB ready (312 chunks)

INFO:     Started server process [XXXX]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The context warning `n_ctx_seq (16384) < n_ctx_train (262144)` is normal — the model supports 262K but we cap at 16K to fit 8GB VRAM.

---

## Step 3 — Access the Web Interface

Open a browser on any machine on your network:

```
http://ai.local:8000
```

or use the server IP directly:

```
http://10.0.0.X:8000
```

The chat UI loads. Type your question and press Enter.

---

## How It Works

Every query goes through three stages before the model generates a reply:

```
1. USER QUERY
   "What does ts_continuity do?"
         │
         ▼
2. RAG RETRIEVAL
   Query embedded → search ChromaDB → top 5 matching chunks retrieved
   e.g. returns sections from SENSOR_IC.tf, SENSOR_IC.lim, SENSOR_IC.spec
         │
         ▼
3. PROMPT ASSEMBLY
   system prompt + RAG context + conversation history + user question
         │
         ▼
4. INFERENCE
   Qwen3.5-9B reads assembled prompt → streams reply token by token
         │
         ▼
5. REPLY
   Browser receives tokens as they arrive → displayed live
```

The RAG step means the model only sees the most relevant chunks from your files — not the entire test program at once. This keeps the context window usage low and the answers specific to your actual files.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves the chat UI HTML |
| `/stream` | POST | Sends a message, streams token reply |
| `/clear` | POST | Clears conversation history for a session |

**Example curl:**

```bash
# send a question
curl -X POST http://ai.local:8000/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "alex", "message": "what does ts_continuity do?"}'

# clear history
curl -X POST http://ai.local:8000/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id": "alex"}'
```

---

## Configuration

Key settings at the top of `WEBRAG_simple.py`:

```python
MODEL_PATH      = Path.home() / "hugging_face_rag/models/..."  # path to GGUF model
CONTEXT_LEN     = 16384    # token window — reduce if running out of VRAM
MAX_TOKENS      = 4096     # max tokens per reply — reduce if model hangs
N_GPU_LAYERS    = -1       # -1 = all layers on GPU, 0 = CPU only
CHROMA_PATH     = "./chroma_db_v93k"     # RAG database folder
COLLECTION_NAME = "v93k_test_programs"   # ChromaDB collection name
```

Key settings in `WERAG_INGEST.py`:

```python
CHUNK_SIZE      = 256      # tokens per chunk — smaller = more precise retrieval
CHUNK_OVERLAP   = 50       # overlap between chunks — prevents cutting mid-sentence
CHROMA_PATH     = "./chroma_db_v93k"     # must match server config
COLLECTION_NAME = "v93k_test_programs"   # must match server config
```

---

## Adding New Files to the Knowledge Base

1. Copy your files into `v93k_dummy/` in the appropriate subfolder
2. Stop the server
3. Delete and re-ingest:

```bash
rm -rf chroma_db_v93k/
python3 WERAG_INGEST.py ./v93k_dummy/
python3 WEBRAG_simple.py
```

Any file type in the supported list is picked up automatically — no configuration needed.

---

## Troubleshooting

**Server won't start — VRAM error:**
Reduce `N_GPU_LAYERS` to offload some layers to RAM:
```python
N_GPU_LAYERS = 20   # partial GPU offload
```

**Model hangs mid-reply:**
Reduce `MAX_TOKENS`:
```python
MAX_TOKENS = 1024
```

**RAG returns wrong results:**
Re-ingest with smaller chunks:
```python
CHUNK_SIZE = 128
```

**`Failed to fetch` in browser:**
Server not running or wrong IP. Test with:
```bash
curl http://ai.local:8000/
```

**ChromaDB collection empty (0 chunks):**
Ingestion hasn't been run yet or pointed at wrong folder. Run:
```bash
python3 WERAG_INGEST.py ./v93k_dummy/
```

---

*Local AI — no cloud, no API keys, no data leaves the machine.*
