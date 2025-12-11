import sys
import os
from huggingface_hub import hf_hub_download

# Add the project root to the python path so we can import intelligent_reporting
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MODELS_DIR = os.path.join(os.getcwd(), "models")
TEXT_REPO = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
TEXT_FILENAME = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

VISION_REPO = "bartowski/Qwen2-VL-7B-Instruct-GGUF"
VISION_FILENAME = "Qwen2-VL-7B-Instruct-Q4_K_M.gguf"


def download_models():
    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"Checking Text Fallback Model ({TEXT_FILENAME})...")
    text_path = os.path.join(MODELS_DIR, TEXT_FILENAME)
    if not os.path.exists(text_path):
        print(f"Downloading {TEXT_FILENAME} from {TEXT_REPO}...")
        hf_hub_download(repo_id=TEXT_REPO, filename=TEXT_FILENAME, local_dir=MODELS_DIR)
        print("Text Fallback Model ready.")
    else:
        print("Text Fallback Model already exists.")

    print(f"\nChecking Vision Fallback Model ({VISION_FILENAME})...")
    vision_path = os.path.join(MODELS_DIR, VISION_FILENAME)
    if not os.path.exists(vision_path):
        print(f"Downloading {VISION_FILENAME} from {VISION_REPO}...")
        try:
            hf_hub_download(
                repo_id=VISION_REPO, filename=VISION_FILENAME, local_dir=MODELS_DIR
            )
            print("Vision Fallback Model ready.")
        except Exception as e:
            print(f"Failed to download Vision model: {e}")
            print("You may need to verify the filename or repo for Qwen2-VL GGUF.")
    else:
        print("Vision Fallback Model already exists.")

    print("\nAll fallback models are checked/downloaded.")


if __name__ == "__main__":
    download_models()
