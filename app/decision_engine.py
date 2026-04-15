from typing import Union

from app.models import DecisionType


AMBIGUOUS_REFERENCES = {
    "this",
    "that",
    "it",
    "they",
    "those",
    "these",
    "algorithm",
    "paper",
    "theory",
}

HIGH_CONFIDENCE_QA = {
    "what is the capital of australia?": "Canberra.",
    "what is 2 + 2?": "2 + 2 = 4.",
    "who wrote hamlet?": "William Shakespeare wrote Hamlet.",
}


def _normalize_message(message: str) -> str:
    return " ".join(message.strip().lower().split())


def _contains_ambiguous_reference(message: str) -> bool:
    words = set(_normalize_message(message).replace("?", "").replace(",", "").split())
    return any(token in words for token in AMBIGUOUS_REFERENCES)


def decide_response(
    message: str,
    history: list[dict[str, str]],
) -> dict[str, Union[str, float, DecisionType]]:
    normalized = _normalize_message(message)

    if normalized in HIGH_CONFIDENCE_QA:
        return {
            "decision": DecisionType.ANSWER,
            "confidence": 0.95,
            "response": HIGH_CONFIDENCE_QA[normalized],
            "reason": "Matched a known high-confidence question in the MVP ruleset.",
        }

    if _contains_ambiguous_reference(message) and not history:
        return {
            "decision": DecisionType.CLARIFY,
            "confidence": 0.42,
            "response": (
                "I need a bit more context before I answer. Could you clarify what "
                "specific topic, algorithm, paper, or concept you mean?"
            ),
            "reason": "The message appears context-dependent, but this session has no prior context yet.",
        }

    if len(normalized.split()) < 3:
        return {
            "decision": DecisionType.CLARIFY,
            "confidence": 0.5,
            "response": "Could you add a little more detail so I can answer more accurately?",
            "reason": "The message is too short to infer a reliable intent in the MVP ruleset.",
        }

    return {
        "decision": DecisionType.ABSTAIN,
        "confidence": 0.22,
        "response": (
            "I’m not confident enough to answer that accurately yet in this early version. "
            "Please give more context or rephrase the question."
        ),
        "reason": "No high-confidence rule matched, so the safe fallback is to abstain.",
    }
