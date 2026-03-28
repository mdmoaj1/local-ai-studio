from __future__ import annotations

from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """Content generator plugin: transforms user text into an LLM prompt."""

    manifest_id: str
    title: str
    description: str

    @abstractmethod
    def build_prompt(self, user_input: str) -> str:
        """Return the full prompt to send to the causal LM."""
