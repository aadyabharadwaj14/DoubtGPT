import re
from typing import Optional


COUNTRY_REFERENCE_PATTERNS = (
    re.compile(r"\bthis country\b", re.IGNORECASE),
    re.compile(r"\bthat country\b", re.IGNORECASE),
)

CAPITAL_OF_PATTERN = re.compile(r"\bcapital of ([a-zA-Z][a-zA-Z\s-]{1,50})\b", re.IGNORECASE)


def resolve_contextual_references(
    message: str,
    history: list[dict[str, str]],
) -> tuple[str, Optional[dict[str, str]]]:
    if not history:
        return message, None

    country = _extract_recent_country(history)
    if not country:
        return message, None

    resolved_message = message
    replaced = False
    for pattern in COUNTRY_REFERENCE_PATTERNS:
        if pattern.search(resolved_message):
            resolved_message = pattern.sub(country, resolved_message)
            replaced = True

    if not replaced:
        return message, None

    return resolved_message, {
        "reference_resolution": "country_from_history",
        "resolved_entity": country,
        "original_message": message,
        "resolved_message": resolved_message,
    }


def _extract_recent_country(history: list[dict[str, str]]) -> Optional[str]:
    for turn in reversed(history[-6:]):
        match = CAPITAL_OF_PATTERN.search(turn["content"])
        if match:
            return _normalize_entity(match.group(1))
    return None


def _normalize_entity(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    return " ".join(part.capitalize() for part in cleaned.split())
