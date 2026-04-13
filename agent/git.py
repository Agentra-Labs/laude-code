"""Git integration — auto-commit after edits."""

import subprocess
from pathlib import Path


class GitRepo:
    def __init__(self, root: Path):
        self.root = root

    def is_repo(self) -> bool:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.root, capture_output=True, text=True
        )
        return result.returncode == 0

    def status(self) -> str:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.root, capture_output=True, text=True
        )
        return result.stdout.strip()

    def diff(self) -> str:
        result = subprocess.run(
            ["git", "diff"],
            cwd=self.root, capture_output=True, text=True
        )
        return result.stdout.strip()

    def commit(self, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=self.root, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.root, capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Commit failed: {result.stderr.strip()}"
        return result.stdout.strip()

    def recent_log(self, n: int = 5) -> str:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            cwd=self.root, capture_output=True, text=True
        )
        return result.stdout.strip()
