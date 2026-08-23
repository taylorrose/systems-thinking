"""Shared mechanical helpers for the Systemantics micro-node graph.

Mechanical only. Nothing here decides semantic boundaries, titles, or node
types; see `procedural memory/reserve software for mechanical checks.md`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

NODE_DIRS = {
    "axioms": "axiom",
    "explanations": "explanation",
    "effects": "effect",
    "examples": "example",
    "practices": "practice",
}

NODE_TYPES = set(NODE_DIRS.values())

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")

FRONTMATTER_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def parse_scalar(raw: str):
    """Parse one frontmatter value without pulling in a YAML dependency."""
    raw = raw.strip()
    if not raw:
        return ""
    if raw[0] in "[{":
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        inner = raw[1:-1]
        # YAML double-quoted strings escape embedded quotes; the graph uses this
        # for axiom statements such as JUST CALLING IT \"FEEDBACK\" ...
        if raw[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    if raw.isdigit():
        return int(raw)
    return raw


# Characters the capture step strips when turning a statement into a filename.
_FILENAME_STRIP = str.maketrans("", "", '?:/\\"*<>|')


def sanitize_filename(title: str) -> str:
    """The filename a given semantic title is expected to produce.

    Axiom statements legitimately contain '?', ':', '/', quotes, and trailing
    periods, none of which survive into the filename. Comparing a title to its
    sanitized form is what makes filename-title agreement checkable without
    flagging every punctuated axiom.
    """
    cleaned = title.translate(_FILENAME_STRIP)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.rstrip(".").strip()


def split_document(text: str) -> tuple[dict, str]:
    """Return (frontmatter, body). Frontmatter is {} when the file has none."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            meta: dict = {}
            for line in lines[1:idx]:
                match = FRONTMATTER_LINE.match(line)
                if match:
                    meta[match.group(1)] = parse_scalar(match.group(2))
            return meta, "\n".join(lines[idx + 1 :])
    return {}, text


@dataclass
class Node:
    path: Path
    root: Path
    meta: dict
    body: str
    errors: list = field(default_factory=list)

    @property
    def rel(self) -> str:
        return self.path.relative_to(self.root).as_posix()

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def directory(self) -> str:
        return self.path.parent.name

    @property
    def expected_type(self) -> str | None:
        return NODE_DIRS.get(self.directory)

    @property
    def title(self) -> str:
        value = self.meta.get("title", "")
        return value if isinstance(value, str) else str(value)

    @property
    def node_type(self) -> str:
        value = self.meta.get("node_type", "")
        return value if isinstance(value, str) else str(value)

    @property
    def status(self) -> str:
        value = self.meta.get("status", "")
        return value if isinstance(value, str) else str(value)

    @property
    def graph_role(self) -> str:
        value = self.meta.get("graph_role", "")
        return value if isinstance(value, str) else str(value)

    @property
    def heading(self) -> str | None:
        for line in self.body.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return None

    @property
    def body_words(self) -> int:
        return len([w for w in self.body.split() if w.strip("#")])

    def links(self) -> list[tuple[str, str | None]]:
        """All wiki-links as (target, alias)."""
        return [(m.group(1).strip(), m.group(2)) for m in WIKILINK.finditer(self.body)]


def load_graph(root: Path, dirs: list[str] | None = None) -> list[Node]:
    """Load every markdown node under the graph's known directories."""
    nodes: list[Node] = []
    for directory in dirs or list(NODE_DIRS):
        base = root / directory
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta, body = split_document(text)
            nodes.append(Node(path=path, root=root, meta=meta, body=body))
    return nodes


def build_index(nodes: list[Node]) -> dict[str, list[Node]]:
    """Index nodes by both 'dir/stem' and bare 'stem' for link resolution."""
    index: dict[str, list[Node]] = {}
    for node in nodes:
        index.setdefault(f"{node.directory}/{node.stem}", []).append(node)
        index.setdefault(node.stem, []).append(node)
    return index


def resolve_link(target: str, index: dict[str, list[Node]]) -> Node | None:
    """Resolve a wiki-link target, tolerating Obsidian's shortest-path form."""
    target = target.split("#")[0].strip()
    for key in (target, target.rsplit("/", 1)[-1]):
        hits = index.get(key)
        if hits:
            return hits[0]
    return None


def chapter_and_section(contexts) -> tuple[str, str]:
    """Derive (chapter, leaf section) from a source_contexts value."""
    if isinstance(contexts, list):
        raw = contexts[0] if contexts else ""
    else:
        raw = contexts or ""
    raw = str(raw).replace("## ", " > ")
    parts = [p.strip() for p in raw.split(">") if p.strip()]
    if not parts:
        return ("(unknown)", "(unknown)")
    chapter = parts[1] if len(parts) > 1 else parts[0]
    return (chapter, parts[-1])


def first_line(value) -> int:
    """Lowest source line referenced, for stable source-order sorting."""
    items = value if isinstance(value, list) else [value]
    numbers: list[int] = []
    for item in items:
        for chunk in re.findall(r"\d+", str(item)):
            numbers.append(int(chunk))
    return min(numbers) if numbers else 10**9
