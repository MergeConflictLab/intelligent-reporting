import os
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage
from llama_cpp import Llama

MODELS_DIR = os.path.join(os.getcwd(), "models")
TEXT_MODEL_FILENAME = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
VISION_MODEL_FILENAME = "Qwen2-VL-7B-Instruct-Q4_K_M.gguf"

_MODEL_CACHE = {}


class FallbackResponse:
    def __init__(self, content: str):
        self.content = content


class FallbackLLM:
    def __init__(
        self, model_filename: str, task_type: str = "text", temperature: float = 0.1
    ):
        self.model_filename = model_filename
        self.task_type = task_type
        self.temperature = temperature
        self.model_path = os.path.join(MODELS_DIR, self.model_filename)

        self._ensure_model_exists()
        self._load_with_cache()

    def _ensure_model_exists(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file {self.model_path} not found. "
                "Please run `python scripts/download_models.py` to download it."
            )

    def _load_with_cache(self):
        """Load model using cache to avoid reloading from disk."""
        global _MODEL_CACHE

        if self.model_path in _MODEL_CACHE:
            print(f"Loading fallback model {self.model_filename} from CACHE...")
            self.model = _MODEL_CACHE[self.model_path]
            return

        self._load_model()

        _MODEL_CACHE[self.model_path] = self.model

    def _load_model(self):
        print(f"Loading fallback model {self.model_filename} using llama.cpp...")
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=-1,
                n_ctx=16384,
                verbose=False,
                start_match_tokens=True,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load fallback model with llama-cpp: {e}")

    def invoke(self, messages: List[BaseMessage]) -> FallbackResponse:
        llama_messages = []

        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "system"
            content = msg.content

            if self.task_type == "vision" and isinstance(content, list):
                new_content = []
                for item in content:
                    if item["type"] == "text":
                        new_content.append({"type": "text", "text": item["text"]})
                    elif item["type"] == "image_url":
                        new_content.append(item)
                llama_messages.append({"role": role, "content": new_content})
            else:
                llama_messages.append({"role": role, "content": content})

        try:
            response = self.model.create_chat_completion(
                messages=llama_messages,
                temperature=self.temperature,
                max_tokens=2048,
            )
            output_text = response["choices"][0]["message"]["content"]
            return FallbackResponse(output_text)
        except Exception as e:
            print(f"Error during generation: {e}")
            return FallbackResponse("")


def get_fallback_llm(task_type="text", temperature=0.1):
    filename = VISION_MODEL_FILENAME if task_type == "vision" else TEXT_MODEL_FILENAME
    return FallbackLLM(filename, task_type, temperature)
