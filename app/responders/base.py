from abc import ABC, abstractmethod


class BaseResponder(ABC):
    @abstractmethod
    def generate(self, message: str, history: list[dict[str, str]]) -> dict:
        """Generate a structured response for a user message."""
