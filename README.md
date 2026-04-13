# coding-agent

Minimal but powerful coding agent. Built from scratch with the patterns that matter.

## Why

Claude Code is great but closed. Aider is great but complex. This is ~500 lines of core logic that you fully own.

## Key design decisions

- **SEARCH/REPLACE editing** — diff-based edits, not full file rewrites. Lower token cost, fewer hallucinations.
- **Tree-sitter repo map** — structural context without reading every file. The agent knows what functions/classes exist before opening anything.
- **5 tools, no more** — read, edit, write, shell, search. Every extra tool adds confusion.
- **Auto-commit** — every change gets committed so you can always revert.

## Setup

```bash
pip install -e .
export OPENAI_API_KEY=sk-...
```

## Usage

```bash
# Single-shot
ca "add error handling to the login function"

# Interactive
ca

# Specify model
ca --model gpt-4o-mini "refactor this module"

# Work on specific directory
ca --dir /path/to/project "fix the tests"

# Verbose mode (show tool calls)
ca -v "implement caching"
```

## Interactive commands

```
> help        # show commands
> status      # git status
> diff        # git diff
> map         # repo overview
> commit      # manual commit
> quit        # exit
```

## Extending

Add a new tool:

```python
from agent.tools.base import Tool, ToolResult

class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string"},
        },
        "required": ["input"],
    }

    def execute(self, input: str) -> ToolResult:
        return ToolResult(f"Did: {input}")
```

Then register it in `core.py` in the `Agent.__init__` tools list.

## Architecture

```
agent/
├── core.py       # main loop: plan → act → observe
├── context.py    # tree-sitter repo map
├── git.py        # git integration
├── prompts.py    # system prompts
└── tools/
    ├── base.py   # tool abstraction
    ├── read.py   # file reading
    ├── edit.py   # SEARCH/REPLACE editing
    ├── write.py  # new file creation
    ├── shell.py  # command execution
    └── search.py # file/content search
```

## What this doesn't have (yet)

- Multi-file context window management (currently sends full repo map)
- Streaming responses
- Multiple model/provider support (OpenAI only right now)
- Conversation persistence
- Sandboxed execution

These are all straightforward to add when you need them.
