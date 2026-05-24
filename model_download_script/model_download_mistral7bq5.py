from huggingface_hub import snapshot_download
from pathlib import Path

workspace = Path.home() / "hugging_face_rag"
model_path = workspace / "models" / "mistral-7b-q5"

snapshot_download(
    repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    local_dir=str(model_path),
    allow_patterns=["*Q5_K_M*"]  # Download ONLY Q5 quantized	
)
print(f"✅ Downloaded to {model_path}")
