"""
Token counter for OpenClaw Observational Memory.

Simple token estimation for threshold detection.
"""

import re
from typing import List


class TokenCounter:
    """Token counter for observation thresholds."""

    def __init__(self):
        """Initialize token counter."""
        # Simple word-based estimation (more accurate than len(text))
        # Rough estimate: ~4 tokens per word

    def count_observations(self, observations: List) -> int:
        """
        Count tokens for a list of observations.

        Simple word-based estimation:
        - ~4 tokens per word
        - Multiplied by observations count
        """
        if not observations:
            return 0

        total_words = sum(len(obs.content.split()) for obs in observations)
        return total_words * 4

    def count_text(self, text: str) -> int:
        """Count tokens for plain text."""
        words = text.split()
        return len(words) * 4


__all__ = ["TokenCounter"]
