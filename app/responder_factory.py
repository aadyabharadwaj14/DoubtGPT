from app.config import Settings
from app.responders.base import BaseResponder
from app.responders.gemini import GeminiResponder
from app.responders.ollama import OllamaResponder
from app.responders.rule_based import RuleBasedResponder
from app.semantic_similarity import (
    get_ollama_semantic_similarity_scorer,
    get_semantic_similarity_scorer,
)


def build_responder(settings: Settings) -> BaseResponder:
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError(
                "LLM_PROVIDER is set to gemini, but GEMINI_API_KEY is missing."
            )
        semantic_scorer = None
        if settings.semantic_agreement_enabled:
            semantic_scorer = get_semantic_similarity_scorer(
                settings.embedding_model_name
            )
        return GeminiResponder(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            sample_count=settings.gemini_sample_count,
            semantic_scorer=semantic_scorer,
        )

    if provider == "ollama":
        semantic_scorer = None
        if settings.semantic_agreement_enabled:
            semantic_scorer = get_ollama_semantic_similarity_scorer(
                settings.ollama_base_url,
                settings.ollama_embed_model,
            )
        return OllamaResponder(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            sample_count=settings.ollama_sample_count,
            semantic_scorer=semantic_scorer,
        )

    if provider == "rule_based":
        return RuleBasedResponder()

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. "
        "Supported values: gemini, ollama, rule_based."
    )
