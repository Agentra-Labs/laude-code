"""SEARCH/REPLACE diff-based editing. This is the key differentiator."""

import re
from pathlib import Path
from .base import Tool, ToolResult

SEARCH_MARKER = "<<<<<<< SEARCH"
DIVIDER = "======="
REPLACE_MARKER = ">>>>>>> REPLACE"


class EditFile(Tool):
    name = "edit_file"
    description = (
        "Edit a file using SEARCH/REPLACE blocks. "
        "Provide the exact text to find (SEARCH) and the replacement (REPLACE). "
        "Multiple blocks allowed for different edits in one call. "
        "For new files, use write_file instead."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "edits": {
                "type": "string",
                "description": (
                    "SEARCH/REPLACE blocks. Format:\n"
                    "<<<<<<< SEARCH\n"
                    "exact text to find\n"
                    "=======\n"
                    "replacement text\n"
                    ">>>>>>> REPLACE"
                ),
            },
        },
        "required": ["path", "edits"],
    }

    def __init__(self, root: Path):
        self.root = root

    def execute(self, path: str, edits: str) -> ToolResult:
        fp = self.root / path
        if not fp.exists():
            return ToolResult("", error=f"File not found: {path}")

        content = fp.read_text(errors="replace")
        blocks = self._parse_blocks(edits)
        if not blocks:
            return ToolResult("", error="No valid SEARCH/REPLACE blocks found")

        changes = []
        for i, (search, replace) in enumerate(blocks):
            if search == "":
                # Empty search = append
                content = content.rstrip("\n") + "\n" + replace
                changes.append(f"Block {i+1}: appended")
            elif search in content:
                content = content.replace(search, replace, 1)
                changes.append(f"Block {i+1}: replaced")
            else:
                # Fuzzy: strip whitespace and try
                search_norm = "\n".join(l.rstrip() for l in search.splitlines())
                content_norm = "\n".join(l.rstrip() for l in content.splitlines())
                if search_norm in content_norm:
                    idx = content_norm.find(search_norm)
                    lines_before = content_norm[:idx].count("\n")
                    search_lines = search_norm.count("\n") + 1
                    original_lines = content.splitlines()
                    before = original_lines[:lines_before]
                    after = original_lines[lines_before + search_lines:]
                    new_lines = before + replace.splitlines() + after
                    content = "\n".join(new_lines)
                    changes.append(f"Block {i+1}: replaced (whitespace-normalized)")
                else:
                    return ToolResult(
                        "", error=f"Block {i+1}: SEARCH text not found in file"
                    )

        fp.write_text(content)
        return ToolResult(f"Edited {path}: {', '.join(changes)}")

    def _parse_blocks(self, edits: str) -> list[tuple[str, str]]:
        blocks = []
        pattern = re.compile(
            rf"{re.escape(SEARCH_MARKER)}\n(.*?)\n{re.escape(DIVIDER)}\n(.*?)\n{re.escape(REPLACE_MARKER)}",
            re.DOTALL,
        )
        for m in pattern.finditer(edits):
            blocks.append((m.group(1), m.group(2)))
        return blocks
