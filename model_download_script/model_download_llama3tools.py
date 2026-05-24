from huggingface_hub import hf_hub_download
from pathlib import Path

workspace = Path.home() / "hugging_face_rag"
model_path = workspace / "models" / "llama3-groq-8b-tools"
model_path.mkdir(parents=True, exist_ok=True)

hf_hub_download(
    repo_id="bartowski/Llama-3-Groq-8B-Tool-Use-GGUF",
    filename="Llama-3-Groq-8B-Tool-Use-Q4_K_M.gguf",
    local_dir=str(model_path)
)

print(f"✅ Downloaded to {model_path}")