"""
Download all required models.
"""

import sys
import os
from huggingface_hub import hf_hub_download

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MODELS_DIR = os.path.join(os.getcwd(), "models")

# Text model configuration
TEXT_REPO = "bartowski/Llama-3.2-3B-Instruct-GGUF"
TEXT_FILENAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

# Code model configuration
CODE_REPO = "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
CODE_FILENAME = "qwen2.5-coder-3b-instruct-q8_0.gguf"


def download_file_with_retry(repo_id, filename, local_dir, file_description):
    """Download a file with proper error handling."""
    file_path = os.path.join(local_dir, filename)

    if os.path.exists(file_path):
        print(f"✓ {file_description} already exists: {filename}")
        return True

    print(f"⬇️  Downloading {file_description}: {filename}")
    print(f"   Repository: {repo_id}")

    try:
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False,  # Avoid symlink issues
        )
        print(f"✓ {file_description} ready: {filename}\\n")
        return True
    except Exception as e:
        print(f"❌ Failed to download {file_description}: {e}\\n")
        return False


def download_models():
    """Download all required models."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("=" * 70)
    print("MODEL DOWNLOADER")
    print("=" * 70)
    print(f"Target directory: {MODELS_DIR}\\n")

    success_count = 0
    total_files = 2  # 1 text model + 1 code model

    # 1. Text Model
    print("[ 1/2 ] TEXT MODEL")
    print("-" * 70)
    if download_file_with_retry(TEXT_REPO, TEXT_FILENAME, MODELS_DIR, "Text model"):
        success_count += 1

    # 2. Code Model
    print("[ 2/2 ] CODE MODEL")
    print("-" * 70)
    if download_file_with_retry(CODE_REPO, CODE_FILENAME, MODELS_DIR, "Code model"):
        success_count += 1

    # Summary
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Successfully downloaded: {success_count}/{total_files} files\\n")

    if success_count == total_files:
        print("✅ ALL FILES DOWNLOADED SUCCESSFULLY!")
        return 0
    else:
        print("⚠️  SOME FILES FAILED TO DOWNLOAD")
        return 1


if __name__ == "__main__":
    exit_code = download_models()
    sys.exit(exit_code)
