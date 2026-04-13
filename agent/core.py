"""Core agent loop. This is the heart of the system."""

from __future__ import annotations
import json
from pathlib import Path

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from agent.prompts import SYSTEM_PROMPT
from agent.context import RepoMap
from agent.git import GitRepo
from agent.tools.base import Tool, ToolResult
from agent.tools.read import ReadFile
from agent.tools.edit import EditFile
from agent.tools.write import WriteFile
from agent.tools.shell import ShellCommand
from agent.tools.search import SearchFiles

console = Console()


class Agent:
    def __init__(self, root: Path, model: str = "gpt-4o", auto_commit: bool = True, verbose: bool = False):
        self.root = root
        self.model = model
        self.auto_commit = auto_commit
        self.verbose = verbose

        self.client = OpenAI()  # uses OPENAI_API_KEY env var
        self.repo_map = RepoMap(root)
        self.git = GitRepo(root)

        # Register tools
        self.tools: list[Tool] = [
            ReadFile(root),
            EditFile(root),
            WriteFile(root),
            ShellCommand(root),
            SearchFiles(root),
        ]
        self.tool_map = {t.name: t for t in self.tools}

    def run(self, task: str, max_turns: int = 30) -> str:
        """Run the agent loop on a task. Returns the final response."""

        # Build context
        context_parts = []
        context_parts.append(f"Working directory: {self.root}")
        context_parts.append(f"Repo map:\n{self.repo_map.get_overview()}")

        if self.git.is_repo():
            status = self.git.status()
            if status:
                context_parts.append(f"Git status:\n{status}")

        context = "\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nTask: {task}"},
        ]

        openai_tools = [t.to_openai() for t in self.tools]

        console.print(f"\n[bold blue]Task:[/] {task}\n")

        for turn in range(max_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=openai_tools,
                    temperature=0,
                )
            except Exception as e:
                console.print(f"[red]API error: {e}[/]")
                return f"Error: {e}"

            choice = response.choices[0]
            msg = choice.message

            # Show assistant thinking (if there's text content)
            if msg.content:
                console.print(Panel(msg.content, border_style="dim", title="Agent"))

            # Check if done
            if choice.finish_reason == "stop":
                # Auto-commit if enabled
                if self.auto_commit and self.git.is_repo():
                    status = self.git.status()
                    if status:
                        commit_msg = f"agent: {task[:72]}"
                        result = self.git.commit(commit_msg)
                        console.print(f"[green]{result}[/]")
                return msg.content or "Done."

            # Handle tool calls
            if choice.finish_reason == "tool_calls" and msg.tool_calls:
                # Add assistant message
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                })

                for tc in msg.tool_calls:
                    name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    if self.verbose:
                        console.print(f"  [dim]Calling {name}({json.dumps(args, indent=2)})[/]")

                    tool = self.tool_map.get(name)
                    if tool:
                        result = tool.execute(**args)
                        output = result.output if result.ok else f"Error: {result.error}"
                        status_tag = "[green]ok[/]" if result.ok else "[red]error[/]"
                        console.print(f"  {status_tag} {name}: {output[:200]}{'...' if len(output) > 200 else ''}")
                    else:
                        output = f"Unknown tool: {name}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": output,
                    })

        console.print("[yellow]Max turns reached[/]")
        return "Max turns reached."
