"""Read files from the repo."""

from pathlib import Path
from .base import Tool, ToolResult


class ReadFile(Tool):
    name = "read_file"
    description = "Read a file. Use line ranges for large files."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path relative to repo root"},
            "start_line": {"type": "integer", "description": "Start line (1-indexed)", "default": 1},
            "end_line": {"type": "integer", "description": "End line (inclusive)", "default": 500},
        },
        "required": ["path"],
    }

    def __init__(self, root: Path):
        self.root = root

    def execute(self, path: str, start_line: int = 1, end_line: int = 500) -> ToolResult:
        fp = self.root / path
        if not fp.exists():
            return ToolResult("", error=f"File not found: {path}")
        if not fp.is_file():
            return ToolResult("", error=f"Not a file: {path}")
        try:
            lines = fp.read_text(errors="replace").splitlines()
            total = len(lines)
            start = max(0, start_line - 1)
            end = min(total, end_line)
            selected = lines[start:end]
            numbered = [f"{i+start+1:4d} | {line}" for i, line in enumerate(selected)]
            header = f"--- {path} (lines {start+1}-{end} of {total}) ---"
            return ToolResult("\n".join([header] + numbered))
        except Exception as e:
            return ToolResult("", error=str(e))
