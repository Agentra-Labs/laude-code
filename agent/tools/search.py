"""Search files by name or content."""

import re
from pathlib import Path
from .base import Tool, ToolResult


class SearchFiles(Tool):
    name = "search_files"
    description = "Search for text in files or find files by name pattern."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "glob": {"type": "string", "description": "File glob filter (e.g. '*.py')", "default": "*"},
            "mode": {
                "type": "string",
                "enum": ["content", "filename"],
                "description": "Search inside files or by filename",
                "default": "content",
            },
            "max_results": {"type": "integer", "default": 30},
        },
        "required": ["pattern"],
    }

    def __init__(self, root: Path):
        self.root = root

    def execute(self, pattern: str, glob: str = "*", mode: str = "content", max_results: int = 30) -> ToolResult:
        if mode == "filename":
            matches = sorted(self.root.rglob(glob))
            regex = re.compile(pattern, re.IGNORECASE)
            found = [str(m.relative_to(self.root)) for m in matches if regex.search(m.name)]
            return ToolResult("\n".join(found[:max_results]) or "No matches")

        # Content search
        regex = re.compile(pattern, re.IGNORECASE)
        results = []
        skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        for fp in self.root.rglob(glob):
            if any(s in fp.parts for s in skip):
                continue
            if not fp.is_file():
                continue
            try:
                for i, line in enumerate(fp.read_text(errors="replace").splitlines(), 1):
                    if regex.search(line):
                        rel = str(fp.relative_to(self.root))
                        results.append(f"{rel}:{i}: {line.rstrip()}")
                        if len(results) >= max_results:
                            break
            except Exception:
                continue
            if len(results) >= max_results:
                break
        return ToolResult("\n".join(results) or "No matches")
