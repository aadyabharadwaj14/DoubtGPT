import os
from dataclasses import dataclass
from typing import Optional


try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during early setup
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "rule_based")
    database_path: str = os.getenv("DATABASE_PATH", "data/doubtgpt.sqlite3")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_sample_count: int = int(os.getenv("GEMINI_SAMPLE_COUNT", "3"))
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    ollama_sample_count: int = int(os.getenv("OLLAMA_SAMPLE_COUNT", "3"))
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    semantic_agreement_enabled: bool = (
        os.getenv("SEMANTIC_AGREEMENT_ENABLED", "true").lower() == "true"
    )
    fast_path_enabled: bool = (
        os.getenv("FAST_PATH_ENABLED", "true").lower() == "true"
    )


def get_settings() -> Settings:
    return Settings()
