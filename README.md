# V93K RAG Assistant

A local, offline AI assistant for Advantest V93000 SmarTest 7 test program development.
Built on Qwen3.5-9B Q4, ChromaDB, and FastAPI — runs entirely on your machine with no cloud dependency.

---

## What It Does

The V93K RAG Assistant is a local AI knowledge base for semiconductor test program development on the Advantest V93000 platform. It holds and actively cross-references a broad range of technical information — test program files, device specifications, functional descriptions, DFT methodologies, wafer sort best practices, and accumulated engineering know-how from previous projects in the same device family.

Unlike a simple document search, the assistant understands how information connects across files. It knows that a test suite in the testflow references a levelset, a timingset, a pin group, a spec limit, a C++ test method class, and a bin assignment — and when you ask a question or request a change, it reasons across all of those dependencies simultaneously.

**What the knowledge base carries:**

- **Test program files** — complete interconnected set: `.tf` testflow, `.lim` limit table, `.spec` named limits, `.pin` pin groups and channel map, `.lvl` voltage corners, `.tim` timing sets, `.vec` ASCII patterns, and `.cpp` C++ test method implementations
- **Device specification** — DUT electrical characteristics, register maps, operating modes, self-test behavior, and interface protocols
- **DFT knowledge** — scan chain structure, ATPG pattern strategy, IDDQ methodology, continuity approach, and structural vs functional test coverage decisions
- **Wafer sort best practices** — bin assignment strategy, contact verification flow, on-fail logic, site parallelism, and yield-aware test ordering
- **Family knowledge** — best practices developed across previous devices in the same product family, reusable test method patterns, and known failure modes that inform limit setting

This accumulated knowledge allows the assistant to do more than answer questions. It can generate new tests consistent with the existing program structure, explain why a test was designed a certain way, flag cross-file inconsistencies, and apply lessons from one project to the next as additional device knowledge is added to the database.

**Current example:** a 3-axis SPI accelerometer — complete test program and device knowledge base including testflow, all configuration files, C++ test methods covering continuity through MEMS self-test, and supporting documentation. All example materials were sourced from publicly available references.

**Example queries:**

```
"Review ts_scan_full for cross-file issues"
"What levelset does ts_idd_active use and what are the VDD voltages?"
"Generate a new IDD test for standby mode using the same pattern as ts_idd_active"
"What DFT approach does this program use for structural coverage?"
"Look at the SPI max frequency test — I need to create a new test using the same method,
 writing calibration data to registers at 1.05V supply and 1MHz SPI clock.
 Present all required changes in every affected file before applying any updates."
"We need a new levelset at 1.05V for low-voltage calibration write testing —
 show me what changes are needed in .lvl, .tim, .tf, .lim, and .spec
 before I approve anything."
```

The last two examples demonstrate the assistant's core workflow for new test creation — it surfaces all cross-file dependencies and shows exact changes first, waiting for approval before committing anything. This prevents inconsistent updates where a test exists in the testflow but its spec, bin, or levelset definitions are missing.

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
python3 WEBRAG_simple.py
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

## Step 3 — Open the Assistant in Your Browser

On any machine on your network open a browser and go to:

```
http://ai.local:8000
```

The V93K RAG Assistant chat interface loads automatically.

**Using the assistant:**

- Type your question in the input box at the bottom
- Press **Enter** to send
- The reply streams in live — token by token as the model generates it
- Press **Clear** to reset the conversation and start fresh

**If `ai.local` does not resolve**, use the server IP address directly:

```
http://10.0.0.X:8000
```

Replace `10.0.0.X` with the actual IP of the machine running `WEBRAG_simple.py`. Find it with:

```bash
ip addr | grep "inet " | grep -v 127
```

---

## How It Works

Every query goes through five stages before the reply appears:

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

## Configuration

Key settings at the top of `WEBRAG_simple.py`:

```python
MODEL_PATH      = Path.home() / "hugging_face_rag/models/..."  # path to GGUF model
CONTEXT_LEN     = 16384    # token window — reduce if running out of VRAM
MAX_TOKENS      = 4096     # max tokens per reply
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

**`Failed to fetch` in browser:**
Server not running or wrong IP. Check the server terminal is showing `Uvicorn running on http://0.0.0.0:8000` and try the IP address directly instead of `ai.local`.

**ChromaDB collection empty (0 chunks):**
Ingestion has not been run yet or was pointed at the wrong folder. Run:
```bash
python3 WERAG_INGEST.py ./v93k_dummy/
```

---

*Local AI — no cloud, no API keys, no data leaves the machine.*
