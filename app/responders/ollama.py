import json
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from app.models import DecisionType
from app.responders.base import BaseResponder
from app.uncertainty import aggregate_candidates


class OllamaCandidate(BaseModel):
    decision: DecisionType
    self_confidence: float = Field(..., ge=0.0, le=1.0)
    response: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class OllamaResponder(BaseResponder):
    def __init__(
        self,
        base_url: str,
        model: str,
        sample_count: int = 3,
        semantic_scorer: Optional[object] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
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
            "Return only valid JSON with keys: decision, self_confidence, response, reason.\n"
            "Rules:\n"
            '- decision must be one of: "answer", "clarify", "abstain"\n'
            "- self_confidence must be a number between 0 and 1\n"
            "- If the question is ambiguous or underspecified, prefer clarify\n"
            "- If you are likely to be wrong, prefer abstain\n"
            "- Keep the response concise and helpful\n"
            f"- This is independent sample #{sample_index + 1}; assess it fresh.\n\n"
            f"Conversation history:\n{history_text or '[no prior context]'}\n\n"
            f"Latest user message:\n{message}"
        )

        payload = {
            "model": self._model,
            "prompt": prompt,
            "think": False,
            "format": {
                "type": "object",
                "properties": {
                    "decision": {
                        "type": "string",
                        "enum": ["answer", "clarify", "abstain"],
                    },
                    "self_confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "response": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "decision",
                    "self_confidence",
                    "response",
                    "reason",
                ],
            },
            "stream": False,
            "options": {
                "temperature": 0.7,
            },
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            body = response.json()

        parsed = OllamaCandidate.model_validate(
            json.loads(_extract_json_object(body.get("response", "")))
        )
        return parsed.model_dump()


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]

    raise ValueError(f"Model did not return valid JSON content: {text!r}")
