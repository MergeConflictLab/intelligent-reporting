import os
import atexit
import subprocess
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

MODELS_DIR = os.path.join(os.getcwd(), "models")
TEXT_MODEL_FILENAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
CODE_MODEL_FILENAME = "qwen2.5-coder-3b-instruct-q8_0.gguf"


_MODEL_CACHE = {}


def cleanup_models():
    """Clean up all cached models on exit."""
    global _MODEL_CACHE
    for model_path in list(_MODEL_CACHE.keys()):
        try:
            model = _MODEL_CACHE[model_path]
            if hasattr(model, "close"):
                model.close()
            del _MODEL_CACHE[model_path]
        except:
            pass


atexit.register(cleanup_models)


class FallbackResponse:
    def __init__(self, content: str, usage: Optional[dict] = None):
        self.content = content
        self.usage = usage or {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }


class FallbackLLM:
    def __init__(
        self,
        model_filename: str,
        task_type: str = "text",
        temperature: float = 0.1,
    ):
        self.model_filename = model_filename
        self.task_type = task_type
        self.temperature = temperature
        self.model_path = os.path.join(MODELS_DIR, self.model_filename)
        self.backend = "llamacpp"  # default

        self._ensure_model_exists()
        self._load_with_cache()

    def _ensure_model_exists(self):
        """Verify model file exists."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file {self.model_path} not found.\n"
                "Please run `python scripts/download_models.py` to download it."
            )

    def _try_load_with_llamacpp_text(self):
        """Try to load as text-only model."""
        try:
            from llama_cpp import Llama

            # Auto-detect optimal threads: leave 1 core for system/sidecar
            import multiprocessing

            default_threads = max(1, multiprocessing.cpu_count() - 1)

            n_threads = int(os.getenv("LLAMA_THREADS", default_threads))
            n_ctx = int(os.getenv("LLAMA_CONTEXT_SIZE", 16384))
            n_batch = int(os.getenv("LLAMA_BATCH_SIZE", 512))

            print(
                f"Loading local model with n_threads={n_threads}, n_ctx={n_ctx}, n_batch={n_batch}"
            )

            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=-1,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_batch=n_batch,
                verbose=False,
            )
            self.backend = "llamacpp_text"
            return True

        except Exception:
            return False

    def _try_load_with_llamacpp_cli(self):
        """Try to use llama-cli as a subprocess fallback."""
        try:
            result = subprocess.run(
                ["llama-cli", "--version"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                print("✓ llama-cli available as fallback")
                self.backend = "llamacpp_cli"
                return True
        except:
            pass
        return False

    def _load_with_cache(self):
        """Load model using cache to avoid reloading from disk."""
        global _MODEL_CACHE
        MAX_CACHE_SIZE = 3

        cache_key = f"{self.model_path}:{self.task_type}"

        if cache_key in _MODEL_CACHE:
            print(f"Cache hit for {self.model_filename}")
            self.model = _MODEL_CACHE[cache_key]
            return

        # If cache is full, evict the oldest entry
        if len(_MODEL_CACHE) >= MAX_CACHE_SIZE:
            # Simple FIFO eviction
            key_to_evict = next(iter(_MODEL_CACHE))
            print(
                f"Cache full ({len(_MODEL_CACHE)}/{MAX_CACHE_SIZE}), evicting {key_to_evict}"
            )
            try:
                model = _MODEL_CACHE[key_to_evict]
                if hasattr(model, "close"):
                    model.close()
            except Exception:
                pass
            finally:
                del _MODEL_CACHE[key_to_evict]
                import gc

                gc.collect()

        self._load_model()

        if hasattr(self, "model"):
            _MODEL_CACHE[cache_key] = self.model

    def _load_model(self):
        """Load the model with appropriate settings, trying multiple backends."""
        print(f"Loading fallback model {self.model_filename}...")

        if self._try_load_with_llamacpp_text():
            return

        if self._try_load_with_llamacpp_cli():
            print("\\n⚠️  Using llama-cli subprocess mode (slower)")
            return

        raise RuntimeError(
            f"Failed to load {self.model_filename} with any backend.\\n\\n"
            f"Troubleshooting steps:\\n"
            f"1. Update llama-cpp-python:\\n"
            f"   pip install --upgrade llama-cpp-python\\n"
            f"2. Or with GPU support:\\n"
            f"   CMAKE_ARGS='-DGGML_CUDA=on' pip install --upgrade llama-cpp-python --force-reinstall --no-cache-dir\\n"
            f"3. Check model file integrity:\\n"
            f"   python scripts/download_models.py\\n"
            f"4. Try a different model that's known to work with llama-cpp"
        )

    def invoke(self, messages: List[BaseMessage]) -> FallbackResponse:
        """Invoke the model with the given messages."""

        if self.backend == "llamacpp_cli":
            return self._invoke_with_cli(messages)

        llama_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "assistant"

            content = msg.content

            if isinstance(content, list):
                # Flatten complex content to simple text if possible, ignore images
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                ]
                text_content = " ".join(text_parts)
                if any(item.get("type") == "image_url" for item in content):
                    text_content += "\\n\\n[Note: Image analysis unavailable - analyzing based on text data only]"

                llama_messages.append({"role": role, "content": text_content})
            else:
                llama_messages.append({"role": role, "content": content})

        try:
            response = self.model.create_chat_completion(
                messages=llama_messages,
                temperature=self.temperature,
                max_tokens=2048,
            )
            output_text = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            return FallbackResponse(output_text, usage)

        except Exception as e:
            print(f"Error during generation: {e}")

            return FallbackResponse(
                f"Error generating response: {str(e)}\\n\\n"
                f"Backend: {self.backend}\\n"
                f"Task type: {self.task_type}"
            )

    def _invoke_with_cli(self, messages: List[BaseMessage]) -> FallbackResponse:
        """Fallback to llama-cli subprocess."""
        prompt_parts = []
        for msg in messages:
            content = msg.content
            if isinstance(content, str):
                prompt_parts.append(content)
            elif isinstance(content, list):
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                ]
                prompt_parts.append(" ".join(text_parts))

        prompt = "\\n\\n".join(prompt_parts)

        try:
            result = subprocess.run(
                [
                    "llama-cli",
                    "-m",
                    self.model_path,
                    "-p",
                    prompt,
                    "-n",
                    "2048",
                    "--temp",
                    str(self.temperature),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return FallbackResponse(result.stdout)
        except Exception as e:
            return FallbackResponse(f"CLI fallback error: {e}")

    def close(self):
        """Explicitly close the model."""
        if hasattr(self, "model") and hasattr(self.model, "close"):
            try:
                self.model.close()
            except:
                pass


def get_fallback_llm(task_type="text", temperature=0.1):
    """Get a fallback LLM for the specified task type."""
    if task_type == "code":
        return FallbackLLM(
            CODE_MODEL_FILENAME, task_type="code", temperature=temperature
        )
    else:
        # Default for text and any other type
        return FallbackLLM(
            TEXT_MODEL_FILENAME, task_type="text", temperature=temperature
        )
