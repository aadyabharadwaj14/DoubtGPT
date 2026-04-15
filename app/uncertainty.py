import re
from collections import Counter
from typing import Optional

from app.models import DecisionType
from app.semantic_similarity import SemanticSimilarityScorer


def _normalize_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def lexical_response_agreement(candidates: list[dict]) -> float:
    if len(candidates) < 2:
        return 1.0

    similarities: list[float] = []
    token_sets = [_normalize_tokens(candidate["response"]) for candidate in candidates]

    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            union = left | right
            similarity = len(left & right) / len(union) if union else 1.0
            similarities.append(similarity)

    return sum(similarities) / len(similarities)


def response_agreement(
    candidates: list[dict],
    semantic_scorer: Optional[SemanticSimilarityScorer] = None,
) -> tuple[float, str]:
    lexical_agreement = lexical_response_agreement(candidates)
    if semantic_scorer is None:
        return lexical_agreement, "lexical"

    texts = [candidate["response"] for candidate in candidates]
    try:
        semantic_agreement = semantic_scorer.average_similarity(texts)
    except Exception:
        return lexical_agreement, "lexical_fallback"

    blended_agreement = (0.7 * semantic_agreement) + (0.3 * lexical_agreement)
    blended_agreement = max(0.0, min(1.0, blended_agreement))
    return blended_agreement, "semantic_blend"


def aggregate_candidates(
    candidates: list[dict],
    semantic_scorer: Optional[SemanticSimilarityScorer] = None,
) -> dict:
    if not candidates:
        raise ValueError("At least one candidate is required for aggregation.")

    decision_counts = Counter(candidate["decision"] for candidate in candidates)
    top_decision, top_count = decision_counts.most_common(1)[0]
    decision_consensus = top_count / len(candidates)
    avg_self_confidence = sum(
        candidate["self_confidence"] for candidate in candidates
    ) / len(candidates)
    agreement, agreement_method = response_agreement(candidates, semantic_scorer)

    combined_confidence = (
        0.45 * decision_consensus
        + 0.35 * agreement
        + 0.20 * avg_self_confidence
    )
    combined_confidence = max(0.0, min(1.0, combined_confidence))

    final_decision, reason = choose_final_decision(
        majority_decision=top_decision,
        combined_confidence=combined_confidence,
        decision_consensus=decision_consensus,
        agreement=agreement,
    )
    final_response = select_representative_response(candidates, final_decision)

    return {
        "decision": final_decision,
        "confidence": round(combined_confidence, 3),
        "response": final_response["response"],
        "reason": reason,
        "debug": {
            "candidates": candidates,
            "decision_consensus": round(decision_consensus, 3),
            "response_agreement": round(agreement, 3),
            "agreement_method": agreement_method,
            "average_self_confidence": round(avg_self_confidence, 3),
            "majority_decision": top_decision,
        },
    }


def choose_final_decision(
    majority_decision: DecisionType,
    combined_confidence: float,
    decision_consensus: float,
    agreement: float,
) -> tuple[DecisionType, str]:
    if combined_confidence < 0.35 or agreement < 0.15:
        return (
            DecisionType.ABSTAIN,
            "Candidate responses were too uncertain or inconsistent, so the system abstained.",
        )

    if majority_decision == DecisionType.ANSWER and combined_confidence >= 0.7:
        return (
            DecisionType.ANSWER,
            "Multiple candidates agreed strongly enough to answer.",
        )

    if majority_decision == DecisionType.ABSTAIN and decision_consensus >= 0.67:
        return (
            DecisionType.ABSTAIN,
            "Most candidates preferred abstaining, so the system chose the safer option.",
        )

    return (
        DecisionType.CLARIFY,
        "The system found partial confidence but not enough certainty for a direct answer.",
    )


def select_representative_response(candidates: list[dict], decision: DecisionType) -> dict:
    matching = [candidate for candidate in candidates if candidate["decision"] == decision]
    pool = matching or candidates
    return max(pool, key=lambda candidate: candidate["self_confidence"])
