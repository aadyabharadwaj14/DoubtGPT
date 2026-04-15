from app.decision_engine import decide_response
from app.responders.base import BaseResponder


class RuleBasedResponder(BaseResponder):
    def generate(self, message: str, history: list[dict[str, str]]) -> dict:
        return decide_response(message, history)
