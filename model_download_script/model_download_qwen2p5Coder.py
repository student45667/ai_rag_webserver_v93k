from huggingface_hub import hf_hub_download
from pathlib import Path

workspace   = Path.home() / "hugging_face_rag"
model_path  = workspace / "models" / "qwen2.5-coder-7b-q4"
model_path.mkdir(parents=True, exist_ok=True)

hf_hub_download(
    repo_id="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
    filename="qwen2.5-coder-7b-instruct-q4_k_m.gguf",
    local_dir=str(model_path)
)

print(f"✅ Downloaded to {model_path}")