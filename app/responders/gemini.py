import json
from typing import Optional

from pydantic import BaseModel, Field

from app.models import DecisionType
from app.responders.base import BaseResponder
from app.semantic_similarity import SemanticSimilarityScorer
from app.uncertainty import aggregate_candidates


class GeminiCandidate(BaseModel):
    decision: DecisionType
    self_confidence: float = Field(..., ge=0.0, le=1.0)
    response: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class GeminiResponder(BaseResponder):
    def __init__(
        self,
        api_key: str,
        model: str,
        sample_count: int = 3,
        semantic_scorer: Optional[SemanticSimilarityScorer] = None,
    ) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depends on installed extras
            raise RuntimeError(
                "Gemini support requires the google-genai package. "
                "Install the project dependencies again."
            ) from exc

        self._client = genai.Client(api_key=api_key)
        self._types = types
        self._model = model
        self._sample_count = sample_count
        self._semantic_scorer = semantic_scorer

    def generate(self, message: str, history: list[dict[str, str]]) -> dict:
        history_text = "\n".join(
            f"{turn['role']}: {turn['content']}" for turn in history[-6:]
        )
        candidates = [
            self._generate_candidate(message, history_text, sample_index)
            for sample_index in range(self._sample_count)
        ]
        return aggregate_candidates(candidates, semantic_scorer=self._semantic_scorer)

    def _generate_candidate(
        self,
        message: str,
        history_text: str,
        sample_index: int,
    ) -> dict:
        prompt = (
            "You are DoubtGPT, a confidence-aware assistant.\n"
            "Assess the latest user message independently and conservatively.\n"
            "Use the conversation history if it helps disambiguate the message.\n"
            "Return a JSON object with keys: decision, self_confidence, response, reason.\n"
            "Rules:\n"
            "- decision must be one of: answer, clarify, abstain\n"
            "- self_confidence must be a number between 0 and 1\n"
            "- If the question is ambiguous or underspecified, prefer clarify\n"
            "- If you are likely to be wrong, prefer abstain\n"
            "- Keep the response concise and helpful\n"
            f"- This is independent sample #{sample_index + 1}; assess it fresh.\n\n"
            f"Conversation history:\n{history_text or '[no prior context]'}\n\n"
            f"Latest user message:\n{message}"
        )

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=GeminiCandidate,
            ),
        )
        parsed = GeminiCandidate.model_validate(json.loads(response.text))
        return parsed.model_dump()
