#!/usr/bin/env python3
"""Mechanical integrity checks for the Systemantics micro-node graph.

Covers exactly the checks `procedural memory/reserve software for mechanical
checks.md` assigns to software: frontmatter, allowed node types,
filename-title agreement, required provenance, resolvable links, expected
directories, duplicate titles, orphaned files, missing parent relations, and
known workflow-label anti-patterns.

It makes no semantic judgement. It cannot tell you whether a title states a
complete idea or whether a router reads as a line of reasoning; those stay with
the semantic and source reviewers.

Usage:
  validate_graph.py --root output/systemantics-micro-nodes            # corpus
  validate_graph.py --root ... --scope axioms/FOO.md explanations/Bar.md
  validate_graph.py --root ... --json report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from graphlib import (  # noqa: E402
    NODE_DIRS,
    NODE_TYPES,
    Node,
    build_index,
    load_graph,
    resolve_link,
    sanitize_filename,
)

AXIOM_REQUIRED = [
    "title",
    "status",
    "source_document",
    "source_sha256",
    "source_statement_lines",
    "source_content_ranges",
]
ROUTER_REQUIRED = AXIOM_REQUIRED + ["node_type"]
CHILD_REQUIRED = [
    "title",
    "node_type",
    "parent_axiom",
    "source_document",
    "source_sha256",
    "source_support_ranges",
]

ANTIPATTERN_TITLE = re.compile(
    r"""^(
        captured\s+passage | transition | supporting\s+material | source\s+notes |
        overview | summary | notes | misc(ellaneous)? | context | background |
        (step|phase|part|batch|section)\s+\d+ | introduction | appendix
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)

ROUTER_STATUS = "semantic-router"
RANGE_KEYS = ("source_content_ranges", "source_statement_lines", "source_support_ranges")
PARENT_LINK = re.compile(r"\[\[([^\]|]+)")


def parse_lines(value) -> set[int]:
    """Expand numeric provenance entries such as ``1317-1319``."""
    out: set[int] = set()
    items = value if isinstance(value, list) else [value]
    for item in items:
        if item is None:
            continue
        text = str(item)
        for lo, hi in re.findall(r"(\d+)\s*-\s*(\d+)", text):
            out.update(range(int(lo), int(hi) + 1))
        text = re.sub(r"\d+\s*-\s*\d+", "", text)
        out.update(int(n) for n in re.findall(r"\d+", text))
    return out


def parent_targets(node: Node) -> tuple[list[str], str]:
    """Return declared parent targets and their canonical encoding form."""
    value = node.meta.get("parent_axiom")
    if value is None:
        return [], "absent"
    if isinstance(value, list):
        return [hit for item in value for hit in PARENT_LINK.findall(str(item))], "list"
    hits = PARENT_LINK.findall(str(value))
    return hits, "joined" if len(hits) > 1 else "single"


def semantic_key(value: str) -> str:
    """Compare title substitutions while ignoring case and punctuation."""
    return " ".join(re.findall(r"\w+", value.casefold(), flags=re.UNICODE))


class Report:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def error(self, path: str, check: str, detail: str) -> None:
        self.errors.append({"file": path, "check": check, "detail": detail})

    def warn(self, path: str, check: str, detail: str) -> None:
        self.warnings.append({"file": path, "check": check, "detail": detail})


def check_node(node: Node, index: dict, report: Report) -> None:
    path = node.rel

    if not node.meta:
        report.error(path, "frontmatter", "missing or unparseable frontmatter block")
        return

    # The procedural-parent layer (SYSTEM THINKING entry points) is a separate
    # layer with its own schema; only its links are checked.
    procedural = node.graph_role == "procedural-parent"

    is_axiom = node.directory == "axioms"
    is_router = is_axiom and node.status == ROUTER_STATUS

    # --- expected directory / node type -----------------------------------
    expected = node.expected_type
    if expected is None:
        report.error(path, "directory", f"'{node.directory}/' is not a graph directory")
    if node.node_type and node.node_type not in NODE_TYPES:
        report.error(
            path,
            "node_type",
            f"'{node.node_type}' is not one of {sorted(NODE_TYPES)}",
        )
    elif node.node_type and expected and node.node_type != expected:
        report.error(
            path,
            "node_type",
            f"node_type '{node.node_type}' does not match directory '{node.directory}/'",
        )

    # --- required frontmatter ---------------------------------------------
    if not procedural:
        if is_router:
            required = ROUTER_REQUIRED
        elif is_axiom:
            required = AXIOM_REQUIRED
        else:
            required = CHILD_REQUIRED
        for key in required:
            if key not in node.meta or node.meta[key] in ("", [], None):
                report.error(path, "provenance", f"missing required key '{key}'")

        for key in RANGE_KEYS:
            if key not in node.meta:
                continue
            value = node.meta[key]
            items = value if isinstance(value, list) else [value]
            if any(item is None or str(item).strip().lower() in ("", "null") for item in items):
                report.error(path, "provenance", f"'{key}' contains an empty or null member")
            elif not parse_lines(value):
                report.error(path, "provenance", f"'{key}' contains no numeric source lines")

    # --- filename / title / heading agreement -----------------------------
    if node.title and sanitize_filename(node.title) != node.stem:
        report.error(
            path,
            "filename-title",
            f"filename {node.stem!r} does not match title "
            f"{node.title!r} (expected {sanitize_filename(node.title)!r})",
        )
    heading = node.heading
    if heading is None:
        report.error(path, "heading", "no H1 heading")
    elif node.title and heading != node.title:
        report.error(path, "heading", f"H1 {heading!r} != title {node.title!r}")

    # --- anti-pattern titles ----------------------------------------------
    if not procedural and not is_axiom and ANTIPATTERN_TITLE.match(node.stem):
        report.error(
            path,
            "antipattern-title",
            f"{node.stem!r} names a source bucket or workflow step, not an idea",
        )

    # --- parent relation ---------------------------------------------------
    if not procedural and not is_axiom:
        targets, parent_form = parent_targets(node)
        if not targets:
            report.error(path, "parent", "parent_axiom is not a wiki-link")
        elif len(targets) == 1 and parent_form != "single":
            report.error(path, "parent-format", "one parent must be encoded as one wiki-link string")
        elif len(targets) > 1 and parent_form != "list":
            report.error(path, "parent-format", "multiple parents must be encoded as a list of wiki-link strings")
        for target in targets:
            if resolve_link(target, index) is None:
                report.error(path, "parent", f"parent_axiom {target!r} does not resolve")

    # --- example -> illustrates relation -----------------------------------
    # Established convention in the accepted gold nodes: an example names the
    # explanation it illustrates. It lives in frontmatter, so the body link
    # check above never sees it.
    if not procedural and node.directory == "examples":
        illustrates = str(node.meta.get("illustrates", ""))
        targets = re.findall(r"\[\[([^\]|]+)", illustrates)
        if not targets:
            report.error(path, "illustrates", "example has no 'illustrates' wiki-link")
        for target in targets:
            if resolve_link(target, index) is None:
                report.error(path, "illustrates", f"illustrates {target!r} does not resolve")

    # --- link resolution ---------------------------------------------------
    for target, alias in node.links():
        hit = resolve_link(target, index)
        if hit is None:
            report.error(path, "broken-link", f"[[{target}]] does not resolve")
        elif alias is not None and not alias.strip():
            report.warn(path, "empty-alias", f"[[{target}|]] has an empty alias")
        elif is_router and alias is not None and semantic_key(alias) != semantic_key(hit.title):
            report.error(
                path,
                "title-substitution",
                f"alias {alias!r} changes the linked title {hit.title!r}; "
                "router links must substitute their titles directly",
            )

    # --- router shape (mechanical only) ------------------------------------
    if is_router:
        child_links = [
            t for t, _ in node.links() if t.split("/")[0] in NODE_DIRS and "axioms/" not in t
        ]
        if not child_links:
            report.error(path, "router", "status is semantic-router but links no children")
        unlinked_words = len(re.sub(r"\[\[[^\]]*\]\]", "", node.body).split())
        if unlinked_words > 60:
            report.warn(
                path,
                "router-prose",
                f"{unlinked_words} unlinked words; routers normally carry only "
                "grammar and transitions",
            )
    elif is_axiom and node.status == "unlinked":
        report.warn(path, "pending", "still status: unlinked (not yet decomposed)")


def corpus_checks(nodes: list[Node], report: Report) -> None:
    """Checks that only make sense with the whole graph loaded."""
    by_title: dict[str, list[str]] = {}
    for node in nodes:
        by_title.setdefault(node.stem.casefold(), []).append(node.rel)
    for title, paths in sorted(by_title.items()):
        if len(paths) > 1:
            report.error(
                paths[0],
                "duplicate-title",
                f"title also used by: {', '.join(paths[1:])}",
            )

    linked: set[str] = set()
    index = build_index(nodes)
    routers = [
        node for node in nodes
        if node.directory == "axioms" and node.status == ROUTER_STATUS
    ]
    axioms = {node.stem: node for node in nodes if node.directory == "axioms"}
    linked_by: dict[str, set[str]] = defaultdict(set)
    # Attribute every recursively reachable child to the axiom that exposes it.
    # Progressive disclosure is allowed to continue below the first child; a
    # grandchild is not an orphan merely because the axiom does not flatten it
    # into the top-level router.
    for router in routers:
        queue: list[tuple[Node, int]] = [(router, 0)]
        visited: set[str] = set()
        while queue:
            current, depth = queue.pop()
            if current.rel in visited:
                continue
            visited.add(current.rel)
            for target, _ in current.links():
                hit = resolve_link(target, index)
                if hit is None or hit.directory == "axioms":
                    continue
                declared_targets, _ = parent_targets(hit)
                declared_stems = {target.rsplit("/", 1)[-1] for target in declared_targets}
                # A direct router link is always evidence of an actual edge so
                # omissions in parent_axiom remain detectable. Below the first
                # layer, follow only nodes that explicitly belong to this axiom;
                # reusable practices may cite other concepts without adopting
                # them into every parent's decomposition tree.
                if depth > 0 and router.stem not in declared_stems:
                    continue
                linked.add(hit.rel)
                linked_by[hit.rel].add(router.stem)
                queue.append((hit, depth + 1))

    for node in nodes:
        if node.directory == "axioms" or node.graph_role == "procedural-parent":
            continue
        if node.rel not in linked:
            report.error(
                node.rel,
                "orphan",
                "no axiom router links to this child node",
            )

        targets, _ = parent_targets(node)
        declared: set[str] = set()
        for target in targets:
            hit = resolve_link(target, index)
            if hit is not None:
                declared.add(hit.stem)
        actual = linked_by.get(node.rel, set())
        for parent in sorted(declared - actual):
            report.error(node.rel, "parent-reciprocity", f"names parent {parent!r}, but that router does not link this node")
        for parent in sorted(actual - declared):
            report.error(node.rel, "parent-reciprocity", f"router {parent!r} links this node, but parent_axiom omits it")

        support = parse_lines(node.meta.get("source_support_ranges"))
        allowed: set[int] = set()
        for parent in declared:
            axiom = axioms.get(parent)
            if axiom is not None:
                allowed |= parse_lines(axiom.meta.get("source_statement_lines"))
                allowed |= parse_lines(axiom.meta.get("source_content_ranges"))
        outside = sorted(support - allowed)
        if support and allowed and outside:
            report.error(
                node.rel,
                "provenance-containment",
                f"source support {outside} falls outside all declared parent ranges",
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument(
        "--scope",
        nargs="*",
        default=None,
        metavar="REL_PATH",
        help="limit per-file reporting to these paths (corpus still loaded for "
        "link resolution); corpus-wide checks are skipped unless --corpus",
    )
    ap.add_argument("--corpus", action="store_true", help="force corpus-wide checks")
    ap.add_argument("--json", type=Path, help="also write the report as JSON")
    ap.add_argument("--quiet", action="store_true", help="suppress warnings")
    args = ap.parse_args()

    root = args.root.resolve()
    nodes = load_graph(root)
    if not nodes:
        print(f"error: no nodes found under {root}", file=sys.stderr)
        return 2

    index = build_index(nodes)
    report = Report()

    scope = set(args.scope or [])
    targets = [n for n in nodes if not scope or n.rel in scope]
    if scope:
        missing = scope - {n.rel for n in nodes}
        for rel in sorted(missing):
            report.error(rel, "scope", "scoped path not found in graph")

    for node in targets:
        check_node(node, index, report)

    if args.corpus or not scope:
        corpus_checks(nodes, report)

    routers = sum(1 for n in nodes if n.directory == "axioms" and n.status == ROUTER_STATUS)
    pending = sum(1 for n in nodes if n.directory == "axioms" and n.status == "unlinked")

    print(f"graph: {len(nodes)} nodes | routers: {routers} | pending: {pending}")
    print(f"scope: {len(targets)} file(s) checked")

    for item in report.errors:
        print(f"  ERROR  {item['file']}: [{item['check']}] {item['detail']}")
    if not args.quiet:
        for item in report.warnings:
            print(f"  warn   {item['file']}: [{item['check']}] {item['detail']}")

    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "root": str(root),
                    "nodes": len(nodes),
                    "routers": routers,
                    "pending": pending,
                    "checked": [n.rel for n in targets],
                    "errors": report.errors,
                    "warnings": report.warnings,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
