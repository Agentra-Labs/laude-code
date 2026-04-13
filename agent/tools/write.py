"""Write new files."""

from pathlib import Path
from .base import Tool, ToolResult


class WriteFile(Tool):
    name = "write_file"
    description = "Create a new file with the given content."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "File content"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, root: Path):
        self.root = root

    def execute(self, path: str, content: str) -> ToolResult:
        fp = self.root / path
        if fp.exists():
            return ToolResult("", error=f"File already exists: {path}. Use edit_file to modify.")
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return ToolResult(f"Created {path} ({len(content)} bytes)")
