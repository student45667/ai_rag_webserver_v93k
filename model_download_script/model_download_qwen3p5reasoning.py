from huggingface_hub import hf_hub_download
from pathlib import Path

workspace   = Path.home() / "hugging_face_rag"
model_path  = workspace / "models" / "qwen3.5-9b-q4"
model_path.mkdir(parents=True, exist_ok=True)

hf_hub_download(
    repo_id="bartowski/Qwen_Qwen3.5-9B-GGUF",
    filename="Qwen_Qwen3.5-9B-Q4_K_M.gguf",
    local_dir=str(model_path)
)

print(f"✅ Downloaded to {model_path}")