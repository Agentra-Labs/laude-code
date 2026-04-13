"""Execute shell commands in the repo."""

import subprocess
from pathlib import Path
from .base import Tool, ToolResult


class ShellCommand(Tool):
    name = "run_command"
    description = "Run a shell command in the repo root. Use for tests, builds, git, etc."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run"},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
        },
        "required": ["command"],
    }

    def __init__(self, root: Path):
        self.root = root

    def execute(self, command: str, timeout: int = 30) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            output += f"\n[exit code: {result.returncode}]"
            if len(output) > 8000:
                output = output[:8000] + "\n... (truncated)"
            return ToolResult(output.strip())
        except subprocess.TimeoutExpired:
            return ToolResult("", error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult("", error=str(e))
