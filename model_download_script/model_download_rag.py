from huggingface_hub import snapshot_download
from pathlib import Path

workspace   = Path.home() / "hugging_face_rag"
model_path  = workspace / "models" / "all-MiniLM-L6-v2"
model_path.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    local_dir=str(model_path)
)

print(f"✅ Downloaded to {model_path}")