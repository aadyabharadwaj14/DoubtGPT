from typing import Optional

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
    "subject",
    "topic",
}

QUESTION_STARTERS = {
    "explain",
    "describe",
    "summarize",
    "tell",
    "what",
    "why",
    "how",
}


def _normalize_message(message: str) -> str:
    return " ".join(message.strip().lower().split())


def detect_fast_path(
    message: str,
    history: list[dict[str, str]],
) -> Optional[dict]:
    normalized = _normalize_message(message)
    tokens = normalized.replace("?", "").replace(",", "").split()
    token_set = set(tokens)

    if len(tokens) < 3:
        return {
            "decision": DecisionType.CLARIFY,
            "confidence": 0.93,
            "response": "Could you add a little more detail so I can answer more accurately?",
            "reason": "Fast path triggered because the message is too short to resolve safely.",
            "debug": {
                "fast_path": True,
                "fast_path_rule": "short_message",
            },
        }

    if not history and token_set & AMBIGUOUS_REFERENCES:
        return {
            "decision": DecisionType.CLARIFY,
            "confidence": 0.96,
            "response": (
                "I need a bit more context before I answer. Could you clarify what "
                "specific topic, subject, algorithm, paper, or concept you mean?"
            ),
            "reason": "Fast path triggered because the request is context-dependent and no prior context exists.",
            "debug": {
                "fast_path": True,
                "fast_path_rule": "ambiguous_without_history",
            },
        }

    if (
        not history
        and tokens
        and tokens[0] in QUESTION_STARTERS
        and {"this", "that"} & token_set
    ):
        return {
            "decision": DecisionType.CLARIFY,
            "confidence": 0.94,
            "response": "Could you clarify what you’re referring to so I can answer accurately?",
            "reason": (
                "Fast path triggered because the message contains an unresolved reference "
                "and there is no prior context to ground it."
            ),
            "debug": {
                "fast_path": True,
                "fast_path_rule": "unresolved_reference",
            },
        }

    return None
