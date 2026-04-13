"""CLI entry point for the coding agent."""

import sys
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from agent.core import Agent

console = Console()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Coding Agent")
    parser.add_argument("task", nargs="*", help="Task to perform (if omitted, enters interactive mode)")
    parser.add_argument("--model", default=None, help="Model to use (default: from env or gpt-4o)")
    parser.add_argument("--dir", default=".", help="Working directory")
    parser.add_argument("--no-commit", action="store_true", help="Skip auto-commit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show tool calls")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    model = args.model or os.environ.get("CA_MODEL", "gpt-4o")

    if not (root / ".git").exists():
        console.print("[yellow]Warning:[/] not a git repo. Some features limited.")

    agent = Agent(root=root, model=model, auto_commit=not args.no_commit, verbose=args.verbose)

    console.print(Panel.fit(
        "[bold]Coding Agent[/] — type your task, or 'help' for commands",
        border_style="blue"
    ))

    if args.task:
        # Single-shot mode
        task = " ".join(args.task)
        agent.run(task)
        return

    # Interactive mode
    session = PromptSession(history=InMemoryHistory())
    while True:
        try:
            user_input = session.prompt("\n> ")
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input.strip():
            continue

        cmd = user_input.strip().lower()
        if cmd in ("quit", "exit", "q"):
            break
        elif cmd == "help":
            console.print("""Commands:
  help        Show this help
  status      Git status
  diff        Git diff
  commit      Git commit
  map         Show repo map
  quit/exit   Exit

  Or just type a task and the agent will do it.
""")
        elif cmd == "status":
            from agent.git import GitRepo
            g = GitRepo(root)
            s = g.status()
            console.print(s or "(clean)")
        elif cmd == "diff":
            from agent.git import GitRepo
            g = GitRepo(root)
            d = g.diff()
            console.print(d or "(no changes)")
        elif cmd == "commit":
            from agent.git import GitRepo
            g = GitRepo(root)
            msg = session.prompt("Commit message: ")
            if msg.strip():
                console.print(g.commit(msg))
        elif cmd == "map":
            from agent.context import RepoMap
            rm = RepoMap(root)
            console.print(rm.get_overview())
        else:
            agent.run(user_input)


if __name__ == "__main__":
    main()
