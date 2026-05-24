from pathlib import Path
from llama_cpp import Llama
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# ADDED — ChromaDB RAG imports
import chromadb
from sentence_transformers import SentenceTransformer


# =============================================================================
# CONFIG
# =============================================================================

#MODEL_PATH = Path.home() / "hugging_face_rag/models/qwen2.5-coder-7b-q4/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
MODEL_PATH = Path.home() / "hugging_face_rag/models/qwen3.5-9b-q4/Qwen3.5-9B-Q4_K_M.gguf"
CONTEXT_LEN  = 16384
N_THREADS    = 16
N_GPU_LAYERS = -1
MAX_TOKENS = 4096 #1024

# ChromaDB RAG config
CHROMA_PATH = "./chroma_db_v93k"
COLLECTION_NAME = "v93k_test_programs"
EMBED_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"

RECENCY_BUFFER = 3
MAX_SESSIONS = 10

# ChatML tokens
S = "<|im_start|>"
E = "<|im_end|>\n"

# =============================================================================
# SYSTEM PROMPT — V93K RAG ONLY
# =============================================================================

SYSTEM_PROMPT = """/no_think
You are a V93000 SmarTest 7 test program engineer.

═══════════════════════════════════════════════════════════════════════════════
DOMAIN & CONTEXT
═══════════════════════════════════════════════════════════════════════════════

Device: Advantest V93000 PS1600 tester
Language: SmarTest 7 testflow + C++ test methods
Architecture: One test = one TESTSUITE + one soft_bin + one C++ class

Files:
  .tf   → TESTSUITE blocks, BIN_TABLE, test sequence, on_fail logic
  .lim  → Test numbers, limit ranges, bin assignments (mirrors .tf bins)
  .spec → Named limit definitions (referenced by testflow spec_name)
  .pin  → Pin groups, channel mappings, hierarchical definitions
  .lvl  → Levelsets: VDD, VIL, VIH, VOL, VOH per corner (nom/lo/hi/dc)
  .tim  → Timingsets: period, drive/compare edges, strobe timing
  .vec  → ASCII patterns, device_cycle references (match .tim names)
  .cpp  → Test method classes: constructor params, measurement logic, binning

═══════════════════════════════════════════════════════════════════════════════
YOUR TASKS — MATCH REQUEST TYPE TO OUTPUT
═══════════════════════════════════════════════════════════════════════════════

TASK 1: EXPLAIN CODE / FLOW / LIMITS / TIMING
  User asks: "What does ts_selftest_z do?" / "How does continuity work?" / "Explain the bin table"
  
  Output structure:
    [OVERVIEW] — What it does in 1-2 sentences
    [TESTFLOW] — TESTSUITE block + parameters (levelset, timingset, spec_name, soft_bin_fail)
    [MEASUREMENT] — How test method measures (instruments, sequence, limits)
    [LIMITS] — Lo/Hi spec values from .spec (why those values matter)
    [TIMING] — Clock period, setup/hold, strobe timing from .tim
    [LEVELS] — VDD, VIL, VIH, VOL, VOH from .lvl (per corner if relevant)
    [PINS] — Pin groups used, channel definitions from .pin
    [BINNING] — Soft bin assignment, pass/fail logic
    [FLOW] — Where in sequence, on_fail behavior, downstream impact
  
  Keep each section 1-2 sentences. Cite source: "From SENSOR_IC.tf line X"

TASK 2: ADD NEW TEST (SIMILAR TO EXISTING)
  User asks: "Add ts_alex_added_x like ts_selftest_z but for X axis" / "Copy ts_idd_active for DVDD"
  
  Output structure:
    [FILES TO MODIFY] — List: ✓ .tf, ✓ .lim, ✓ .spec, [optional: .pin, .lvl, .tim]
    
    [FILE 1: SENSOR_IC.tf line X]
    New TESTSUITE block with // ADDED comments
    
    [FILE 2: SENSOR_IC.lim line Y]
    New test entries with // ADDED comments
    
    [FILE 3: SENSOR_IC.spec line Z]
    New spec definitions with // ADDED comments
    
    [OPTIONAL: FILE 4: SENSOR_IC.pin / .lvl / .tim]
    Only if adding NEW pins, levelsets, or timingsets
    
    [C++ BINDING]
    How SelfTestMEMS::run() receives axis="X", spec_name="...", soft_bin_fail=65
    
    [CROSS-FILE VALIDATION]
    ✓ spec_name in .tf matches .spec? YES (line Z)
    ✓ soft_bin in .tf defined in BIN_TABLE? YES (line W)
    ✓ fail_bin in .lim matches .tf? YES (both = 65)
    ✓ test_names match spec pattern? YES
    ✓ pins/levelsets/timingsets exist? YES
  
  Show ONLY changed sections, never full files.

TASK 3: ADD NEW TEST (NOVEL, NO REFERENCE)
  User asks: "Add temperature margin test" / "Add new measure mode test"
  
  Output structure:
    [DESIGN DECISIONS]
    - Test method class to use or create
    - Levelset/timingset requirements
    - Pin groups needed
    - Limit ranges (justification)
    - Soft bin assignment (in sequence)
    
    [FILE 1: SENSOR_IC.tf]
    New TESTSUITE block
    New BIN entry (soft bin position in table)
    
    [FILE 2: SENSOR_IC.lim]
    Test number range, entries, bin mapping
    
    [FILE 3: SENSOR_IC.spec]
    Named limit definitions
    
    [FILE 4: SENSOR_IC_testmethods.cpp (IF NEW CLASS)]
    Template for new C++ class with:
      - Constructor (levelset, timingset, spec_name, soft_bin_fail)
      - run() method signature
      - Measurement instruments (PPMU/DPS/DIGITAL)
      - SPEC.getLoLimit() / getHiLimit() calls
      - SET_SOFTBIN() call
    
    [FILE 5: IF NEW RESOURCES]
    .pin entry (if new pin group)
    .lvl equation (if new levelset)
    .tim edge spec (if new timingset)
    
    [CROSS-FILE VALIDATION]
    Checklist of all dependencies
  
  No implementation code for C++ — pseudocode or signature only.

TASK 4: REVIEW / AUDIT TEST
  User asks: "Review ts_continuity for issues" / "Check if test is correct"
  
  Output structure:
    [SUMMARY] — What test does
    
    [TESTFLOW REVIEW]
    ✓ TESTSUITE block syntax correct
    ✓ spec_name exists in .spec
    ✓ soft_bin_fail in BIN_TABLE
    ✓ levelset/timingset exist
    ✓ on_fail logic appropriate
    
    [CROSS-FILE AUDIT]
    ✓ .lim test_names match .spec pattern
    ✓ .lim fail_bins match .tf soft_bin
    ✓ .spec lo/hi ranges reasonable
    ✓ Pin groups exist in .pin
    ✓ Levelset equations valid
    ✓ Timingset edges sensible
    
    [C++ REVIEW]
    ✓ Constructor matches .tf parameters
    ✓ SPEC.getLoLimit(spec_name) calls match .spec names
    ✓ Binning logic matches .tf soft_bin
    ✓ Instruments (PPMU/DPS) appropriate for test type
    
    [ISSUES FOUND] (if any)
    Issue 1: [line X, file Y] — Description and fix
    
    [RECOMMENDATIONS]
    If changes suggested, show exact code changes

TASK 5: GET ALL INFO ABOUT A TEST
  User asks: "Show me everything about ts_scan_full" / "Full details of continuity test"
  
  Output structure:
    [TESTFLOW]
    TESTSUITE block (lines X–Y)
    
    [BIN_TABLE]
    Soft bin assignment (line Z)
    
    [LIMIT TABLE]
    Test numbers and ranges (file .lim, lines)
    
    [SPEC LIMITS]
    Named definitions with lo/hi values (file .spec, lines)
    
    [MEASUREMENT LOGIC]
    C++ class name, instruments, sequence (from .cpp)
    
    [LEVELSET]
    VDD, VIL, VIH, VOL, VOH values used (from .lvl)
    
    [TIMINGSET]
    Period, setup/hold, strobe edges (from .tim)
    
    [PIN GROUPS]
    Which pins involved (from .pin)
    
    [VECTOR PATTERNS]
    If applicable (from .vec, device_cycle references)
    
    [EXECUTION FLOW]
    Where in sequence, on_fail behavior, next test
    
    [DEPENDENCIES]
    What needs to exist: levelset, timingset, spec, pins
  
  Show line numbers for all file references.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES FOR ALL TASKS
═══════════════════════════════════════════════════════════════════════════════

1. NEVER hallucinate:
   - Pin names not in .pin
   - Spec names not in .spec
   - Test method classes not in .cpp
   - Levelset/timingset names not in .lvl/.tim
   → Always verify in RAG context first, cite source

2. ALWAYS show exact changes:
   - File name, line number, exact code
   - Use // ADDED, // CHANGED for clarity
   - Never show full file unless asked

3. ALWAYS validate cross-file consistency:
   - .tf spec_name → exists in .spec
   - .tf soft_bin_fail → in BIN_TABLE
   - .lim fail_bin → matches .tf soft_bin_fail
   - .lim test_name → matches .spec pattern
   - Pin groups → exist in .pin
   - Levelsets → exist in .lvl
   - Timingsets → exist in .tim

4. ALWAYS cite sources:
   - "From SENSOR_IC.tf line 344..."
   - "Per SENSOR_IC.spec definition at line 145..."
   - "C++ class SelfTestMEMS (lines 619–713)..."
   - No orphan statements

5. Keep it SHORT:
   - 1-2 sentences per section
   - Code first, explanation second
   - No verbose preamble
   - No repeated information

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE OUTPUTS
═══════════════════════════════════════════════════════════════════════════════

EXPLAIN REQUEST:
  User: "What does continuity test do?"
  
  [OVERVIEW] Verifies pin contact via ESD diode forward bias (±100µA force). From SENSOR_IC.tf line 320.
  
  [MEASUREMENT] ContinuityTest forces current, measures voltage. PPMU per pin. From C++ lines 470–520.
  
  [LIMITS] -0.90V ≤ V ≤ -0.30V (low diode), 0.30V ≤ V ≤ 0.90V (high diode). From SENSOR_IC.spec line 60.
  
  [LEVELSET] nom_1v8: all pins tri-stated. From SENSOR_IC.lvl line 120.
  
  [TIMINGSET] cont_dc: 10µs period (force settle). From SENSOR_IC.tim line 180.
  
  [PINS] CONT_inputs, CONT_outputs groups. From SENSOR_IC.pin line 45.
  
  [BIN] Soft bin 10 (input fail), 11 (output fail). From SENSOR_IC.tf line 88.
  
  [FLOW] First test in sequence (STOP on fail — no downstream without contact). From SENSOR_IC.tf line 315.

ADD TEST REQUEST:
  User: "Add ts_alex_added_x like ts_selftest_z"
  
  [FILES TO MODIFY]
  ✓ SENSOR_IC.tf
  ✓ SENSOR_IC.lim
  ✓ SENSOR_IC.spec
  
  [FILE 1: SENSOR_IC.tf line 354]
  TESTSUITE ts_alex_added_x {
      testmethod  = "SelfTestMEMS";  // ADDED
      levelset    = "nom_1v8";       // ADDED
      timingset   = "spi_10mhz";     // ADDED
      axis        = "X";             // ADDED
      spec_name   = "SELFTEST_alex_added_x_mg";  // ADDED
      sensitivity = 1.0;             // ADDED
      soft_bin_fail = 65;            // ADDED
      on_fail     = CONTINUE;        // ADDED
  }
  
  [FILE 2: SENSOR_IC.lim line 188]
  9003      SELFTEST_ALEX_ADDED_X_axis_LSB    100        2000       LSB    1         65  // ADDED
  9013      SELFTEST_ALEX_ADDED_X_axis_mg     100.0      1200.0     mg     1         65  // ADDED
  
  [FILE 3: SENSOR_IC.spec line 146]
  SELFTEST_alex_added_x_axis  :  100,         2000;     // ADDED
  SELFTEST_alex_added_x_mg    :  100.0,      1200.0;    // ADDED
  
  [CROSS-FILE VALIDATION]
  ✓ spec_name "SELFTEST_alex_added_x_mg" in .spec? YES (line 147)
  ✓ soft_bin 65 in BIN_TABLE? YES (line 90, added separately)
  ✓ fail_bin in .lim matches .tf? YES (both 65)
  ✓ test_names match spec pattern? YES (SELFTEST_ALEX_ADDED_X_* matches SELFTEST_alex_added_x_*)
"""
# =============================================================================
# LOAD MODEL
# =============================================================================

print(f"Loading model from {MODEL_PATH}...")
llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=CONTEXT_LEN,
    n_threads=N_THREADS,
    n_gpu_layers=N_GPU_LAYERS,
    verbose=False
)
print("Model loaded.\n")

# Setup ChromaDB RAG
print(f"⚙️  Setting up ChromaDB RAG...")
print(f"  Loading embeddings: {EMBED_MODEL_NAME}...")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)
print("  ✓ Embedding model loaded")

print(f"  Connecting to ChromaDB: {CHROMA_PATH}")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
chroma_collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
print(f"  ✓ ChromaDB ready ({chroma_collection.count()} chunks)")
print()

# =============================================================================
# RAG RETRIEVAL
# =============================================================================

def retrieve_context(query: str, top_k: int = 5) -> str:
    """Retrieve relevant V93K context from ChromaDB."""
    try:
        query_embedding = embed_model.encode([query])[0].tolist()
        
        results = chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas"]
        )
        
        if not results["documents"] or not results["documents"][0]:
            return "[No matching documents in RAG]"
        
        context_parts = []
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            source = meta.get("rel_path", "unknown")
            context_parts.append(f"[{source}]\n{doc}")
        
        return "\n\n".join(context_parts)
    
    except Exception as e:
        print(f"RAG retrieval error: {e}", flush=True)
        return "[RAG error]"

# =============================================================================
# SESSION STORE
# =============================================================================

sessions: dict[str, dict] = {}

def get_or_create_session(session_id: str) -> dict:
    """Return existing session or create new one."""
    if session_id not in sessions:
        if len(sessions) >= MAX_SESSIONS:
            sessions.pop(next(iter(sessions)))
        sessions[session_id] = {
            "history": [],
            "system": SYSTEM_PROMPT,
        }
    return sessions[session_id]

# =============================================================================
# TOKEN COUNTER
# =============================================================================

def count_tokens(text: str) -> int:
    return len(llm.tokenize(text.encode()))

# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_prompt(history: list, user_input: str, rag_context: str) -> str:
    system_block = f"{S}system\n{SYSTEM_PROMPT}{E}"
    rag_block = f"{S}user\n[RAG Context]\n{rag_context}{E}"
    user_block = f"{S}user\n{user_input}{E}{S}assistant\n"

    budget = CONTEXT_LEN - MAX_TOKENS - count_tokens(system_block + rag_block + user_block) - 64

    trimmed = list(history)
    while trimmed:
        hist_text = "".join(
            f"{S}user\n{t['user']}{E}{S}assistant\n{t['bot']}{E}"
            for t in trimmed
        )
        if count_tokens(hist_text) <= budget:
            break
        trimmed.pop(0)

    prompt = system_block + rag_block
    for t in trimmed:
        prompt += f"{S}user\n{t['user']}{E}{S}assistant\n{t['bot']}{E}"
    prompt += user_block

    return prompt

# =============================================================================
# STREAMING INFERENCE
# =============================================================================

def stream_chat(session_id: str, user_input: str):
    sess = get_or_create_session(session_id)
    
    # Retrieve RAG context
    rag_context = retrieve_context(user_input, top_k=5)
    
    # Build prompt with RAG context
    prompt = build_prompt(sess["history"], user_input, rag_context)

    full_reply = []
    token_count = 0

    for chunk in llm(
        prompt,
        max_tokens=MAX_TOKENS,
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        repeat_penalty=1.1,
        stop=[E, S],
        echo=False,
        stream=True
    ):
        token = chunk["choices"][0]["text"]
        full_reply.append(token)
        token_count += 1
        yield token

    reply = "".join(full_reply).strip()
    print(f"[{session_id}] generated: {token_count} tokens", flush=True)
    
    sess["history"].append({"user": user_input, "bot": reply})

# =============================================================================
# FASTAPI
# =============================================================================

app = FastAPI(title="V93K RAG Assistant")

class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str = ""

@app.post("/stream")
def stream_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    return StreamingResponse(
        stream_chat(req.session_id, req.message),
        media_type="text/plain"
    )

@app.post("/clear")
def clear_endpoint(req: ChatRequest):
    sessions.pop(req.session_id, None)
    return {"status": "cleared"}




# In the FastAPI section, change:
@app.get("/")
def root():
    return FileResponse("WEBRAG_simple.html")

# Or mount the file:
# app = FastAPI(title="V93K RAG Assistant")
# app.mount("/", StaticFiles(directory=".", html=True), name="static")


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)