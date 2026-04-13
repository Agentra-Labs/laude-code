"""Tree-sitter based repo map — the context engine.

Gives the agent a structural overview of the codebase without reading every file.
Uses tree-sitter to extract function/class definitions, imports, and structure.
"""

from pathlib import Path

try:
    import tree_sitter_languages
    HAS_TSL = True
except ImportError:
    HAS_TSL = False

LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".rs": "rust",
    ".go": "go", ".java": "java", ".c": "c", ".cpp": "cpp",
    ".h": "c", ".hpp": "cpp", ".rb": "ruby", ".php": "php",
    ".sh": "bash", ".lua": "lua", ".zig": "zig",
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox", ".mypy_cache"}


class RepoMap:
    def __init__(self, root: Path):
        self.root = root

    def get_overview(self, max_files: int = 50) -> str:
        """Get a structural overview of the repo."""
        files = self._discover_files(max_files)
        if not files:
            return "No supported source files found."

        lines = [f"Repo: {self.root.name}", f"Files ({len(files)} shown):", ""]

        for fp in sorted(files):
            rel = str(fp.relative_to(self.root))
            symbols = self._extract_symbols(fp)
            if symbols:
                lines.append(f"{rel}")
                for sym in symbols[:20]:
                    lines.append(f"  {sym}")
                lines.append("")
            else:
                lines.append(f"{rel}")
                lines.append("")

        return "\n".join(lines)

    def get_file_symbols(self, path: str) -> str:
        """Get symbols from a specific file."""
        fp = self.root / path
        if not fp.exists():
            return f"File not found: {path}"
        symbols = self._extract_symbols(fp)
        if not symbols:
            return f"{path}: no structural symbols found"
        return f"{path}:\n" + "\n".join(f"  {s}" for s in symbols)

    def _discover_files(self, max_files: int) -> list[Path]:
        files = []
        for fp in self.root.rglob("*"):
            if any(s in fp.parts for s in SKIP_DIRS):
                continue
            if fp.is_file() and fp.suffix in LANG_MAP:
                files.append(fp)
                if len(files) >= max_files:
                    break
        return files

    def _extract_symbols(self, fp: Path) -> list[str]:
        if not HAS_TSL:
            return self._extract_symbols_regex(fp)

        lang = LANG_MAP.get(fp.suffix)
        if not lang:
            return []

        try:
            parser = tree_sitter_languages.get_parser(lang)
            tree = parser.parse(fp.read_bytes())
            return self._walk_tree(tree.root_node, lang)
        except Exception:
            return self._extract_symbols_regex(fp)

    def _walk_tree(self, node, lang: str) -> list[str]:
        symbols = []
        for child in node.children:
            if child.type in ("function_definition", "method_definition", "function_declaration"):
                name = self._get_name(child)
                if name:
                    symbols.append(f"def {name} (line {child.start_point[0]+1})")
            elif child.type in ("class_definition", "class_declaration"):
                name = self._get_name(child)
                if name:
                    symbols.append(f"class {name} (line {child.start_point[0]+1})")
            elif child.type == "import_statement":
                text = child.text.decode(errors="replace").strip()
                if len(text) < 80:
                    symbols.append(text)
            elif child.type == "import_from_statement":
                text = child.text.decode(errors="replace").strip()
                if len(text) < 80:
                    symbols.append(text)
            if child.type in ("block", "module", "class_body", "class_definition", "decorated_definition"):
                symbols.extend(self._walk_tree(child, lang))
        return symbols

    def _get_name(self, node) -> str | None:
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode(errors="replace")
        return None

    def _extract_symbols_regex(self, fp: Path) -> list[str]:
        """Fallback regex-based extraction when tree-sitter isn't available."""
        symbols = []
        try:
            for i, line in enumerate(fp.read_text(errors="replace").splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("class "):
                    name = stripped.split("(")[0].split(":")[0]
                    symbols.append(f"{name} (line {i})")
                elif stripped.startswith("import ") or stripped.startswith("from "):
                    if len(stripped) < 80:
                        symbols.append(stripped)
        except Exception:
            pass
        return symbols
