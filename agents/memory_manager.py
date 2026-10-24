"""Memory Manager and Context-Window Controller for Multi-Agent Orchestration.

Manages conversational state, sliding window message retention, and automatic
summarization to prevent context overflow while preserving vital research findings.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AgentMemoryManager:
    """Controls context window budgeting, history retention, and compression."""

    def __init__(
        self,
        max_tokens: int = 4000,
        max_entries: int = 10,
        token_counter: Callable[[str], int] | None = None,
        summarizer: Callable[[str], str] | None = None,
    ) -> None:
        """Initialize the memory manager.

        Args:
            max_tokens: Approximate token threshold before triggering compression.
            max_entries: Maximum number of recent detailed turns to hold in raw memory.
            token_counter: Optional custom token counting function (defaults to len // 4).
            summarizer: Optional custom LLM or rule-based summarizer function.
        """
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive.")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive.")

        self.max_tokens = max_tokens
        self.max_entries = max_entries
        self._token_counter = token_counter or self._default_token_counter
        self._summarizer = summarizer or self._default_summarizer

        self.history: list[dict[str, Any]] = []
        self.running_summary: str = ""

    @staticmethod
    def _default_token_counter(text: str) -> int:
        """Estimate tokens as characters // 4 with a minimum of 1 for non-empty text."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def _default_summarizer(text_to_compress: str) -> str:
        """Rule-based summarization fallback for older context entries."""
        lines = [line.strip() for line in text_to_compress.splitlines() if line.strip()]
        if not lines:
            return ""
        # Keep key lines (e.g. status, hypotheses, findings)
        key_lines = [
            line for line in lines
            if any(term in line.lower() for term in ["hypothesis", "finding", "result", "evidence", "review", "p_value", "mean"])
        ]
        if not key_lines:
            key_lines = lines[:5]
        return "Summary of past interactions: " + " | ".join(key_lines[:8])

    def add_interaction(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an interaction turn in memory and compress if bounds are exceeded."""
        if not role or not isinstance(role, str):
            raise ValueError("Role must be a non-empty string.")
        if not isinstance(content, str):
            raise ValueError("Content must be a string.")

        entry = {
            "role": role.strip(),
            "content": content.strip(),
            "metadata": metadata or {},
            "timestamp": time.time(),
            "tokens": self._token_counter(content),
        }
        self.history.append(entry)

        # Check if compression is needed
        if len(self.history) > self.max_entries or self.estimate_total_tokens() > self.max_tokens:
            self.compress()

        return entry

    def estimate_total_tokens(self) -> int:
        """Estimate total tokens across running summary and current active history."""
        summary_tokens = self._token_counter(self.running_summary)
        history_tokens = sum(entry.get("tokens", 0) for entry in self.history)
        return summary_tokens + history_tokens

    def compress(self) -> None:
        """Condense the oldest interactions into the running summary."""
        if len(self.history) <= 2:
            return

        # Keep the most recent half of max_entries
        keep_count = max(2, self.max_entries // 2)
        to_compress = self.history[:-keep_count]
        self.history = self.history[-keep_count:]

        # Format text to summarize
        block_text = "\n".join(
            f"[{entry['role']}]: {entry['content']}"
            for entry in to_compress
        )

        full_compress_text = (
            f"Previous Summary:\n{self.running_summary}\n\nRecent History:\n{block_text}"
            if self.running_summary
            else block_text
        )

        try:
            self.running_summary = self._summarizer(full_compress_text)
        except Exception as exc:
            logger.warning("Summarizer failed during memory compression: %s", exc)
            self.running_summary = self._default_summarizer(full_compress_text)

    def get_context(self, include_metadata: bool = False) -> str:
        """Format the full context (summary + active turns) for prompt injection."""
        sections: list[str] = []

        if self.running_summary:
            sections.append(f"### EXECUTIVE RESEARCH SUMMARY\n{self.running_summary}")

        if self.history:
            history_lines = ["### RECENT RESEARCH INTERACTIONS"]
            for entry in self.history:
                line = f"**{entry['role'].upper()}**: {entry['content']}"
                if include_metadata and entry["metadata"]:
                    meta_str = json.dumps(entry["metadata"], separators=(",", ":"))
                    line += f" (Metadata: {meta_str})"
                history_lines.append(line)
            sections.append("\n".join(history_lines))

        return "\n\n".join(sections)

    def clear(self) -> None:
        """Reset memory and history."""
        self.history.clear()
        self.running_summary = ""
