"""Tool abstraction — every tool is a class with name, description, schema, execute."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    output: str
    error: str | None = None
    metadata: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Tool:
    name: str = ""
    description: str = ""
    parameters: dict = {}  # JSON schema for the tool's parameters

    def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
