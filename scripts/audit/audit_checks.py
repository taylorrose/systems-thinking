#!/usr/bin/env python3
"""ISOLATED, READ-ONLY audit checks for the Systemantics micro-node graph.

This is a calibration surface, deliberately separate from the production
validate_graph.py. It exists because an independent random sample found defects
in routers that validate_graph.py passed as clean. Nothing here writes to the
graph.

Each check below was calibrated against a confirmed real defect:

  NULL_RANGE        source_content_ranges: [null] parsed to [None], which the
                    production emptiness test (`in ("", [], None)`) never
                    caught. Confirmed on THE INFORMATION YOU WANT IS NOT THE
                    INFORMATION YOU NEED.
  FILENAME_TITLE    Filename/title agreement uses the graph's documented
                    filesystem-safe title encoding; punctuation removed by
                    that encoding is not itself a semantic defect.
  PARENT_FORMAT     Three mutually incompatible multi-parent encodings exist
                    (YAML list, space-joined single string, single value).
                    Production code regex-scraped [[...]] from all three.
  PARENT_RECIPROCITY A child names a parent that does not reach it, directly or
                    through a recursive child router, or a router reaches a
                    child that does not name it. Never checked.
  RANGE_CONTAINMENT A child cites source support outside its parent's declared
                    statement/content ranges. Never checked.
Semantic shape is deliberately excluded. A router may carry its description
through an effect or through a legitimately shared explanation; deciding
whether it actually does so requires the procedural-memory review gates.

Usage:
  audit_checks.py --root <graph root> [--json out.json] [--csv out.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphlib import (  # noqa: E402
    NODE_DIRS,
    NODE_TYPES,
    build_index,
    load_graph,
    resolve_link,
    sanitize_filename,
    split_document,
)

RANGE_KEYS = ("source_content_ranges", "source_statement_lines", "source_support_ranges")
WIKI = re.compile(r"\[\[([^\]|]+)")

# Severity: 1 = blocks integration, 2 = must fix before acceptance,
#           3 = review / convention decision
SEVERITY = {
    "NULL_RANGE": 1,
    "MISSING_RANGE": 1,
    "PARENT_RECIPROCITY": 1,
    "PARENT_UNRESOLVED": 1,
    "INVALID_NODE_TYPE": 1,
    "BROKEN_LINK": 1,
    "RANGE_CONTAINMENT": 2,
    "PARENT_FORMAT": 2,
    "HEADING_MISMATCH": 2,
    "SUBLINE_UNREPRESENTABLE": 3,
}


def raw_field(path: Path, key: str) -> str | None:
    """Read a frontmatter field as literal text, before any parsing."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}:"):
            return line[len(key) + 1 :].strip()
        if line.strip() == "---" and line is not None:
            continue
    return None


def parse_lines(value) -> set[int]:
    """Expand range strings such as '1317-1319' into a line-number set."""
    out: set[int] = set()
    items = value if isinstance(value, list) else [value]
    for item in items:
        if item is None:
            continue
        text = str(item)
        for lo, hi in re.findall(r"(\d+)\s*-\s*(\d+)", text):
            out.update(range(int(lo), int(hi) + 1))
        stripped = re.sub(r"\d+\s*-\s*\d+", "", text)
        for single in re.findall(r"\d+", stripped):
            out.add(int(single))
    return out


def parent_targets(node) -> tuple[list[str], str]:
    """Return (parent wiki targets, encoding form) for a child node."""
    value = node.meta.get("parent_axiom")
    if value is None:
        return ([], "absent")
    if isinstance(value, list):
        return ([m for v in value for m in WIKI.findall(str(v))], "yaml-list")
    text = str(value)
    hits = WIKI.findall(text)
    if len(hits) > 1:
        return (hits, "space-joined")
    return (hits, "single")


class Findings:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, code: str, file: str, detail: str, axiom: str = "") -> None:
        self.rows.append(
            {
                "code": code,
                "severity": SEVERITY.get(code, 3),
                "file": file,
                "axiom": axiom,
                "detail": detail,
            }
        )


def audit(root: Path) -> Findings:
    nodes = load_graph(root)
    index = build_index(nodes)
    f = Findings()

    axioms = {n.stem: n for n in nodes if n.directory == "axioms"}
    children = [
        n for n in nodes if n.directory != "axioms" and n.graph_role != "procedural-parent"
    ]
    routers = [n for n in axioms.values() if n.status == "semantic-router"]

    # Which routers reach which children through body links. Supporting nodes
    # may themselves be semantic routers, so direct-link reciprocity would
    # falsely reject legitimate recursive decomposition.
    links_to: dict[str, set[str]] = defaultdict(set)
    for r in routers:
        stack = [r]
        seen: set[str] = set()
        while stack:
            current = stack.pop()
            for target, _ in current.links():
                hit = resolve_link(target, index)
                if hit is None or hit.directory == "axioms" or hit.rel in seen:
                    continue
                declared, _ = parent_targets(hit)
                if f"axioms/{r.stem}" not in declared:
                    continue
                seen.add(hit.rel)
                links_to[hit.rel].add(r.stem)
                stack.append(hit)

    # ---------------- per-node structural checks ----------------
    for n in nodes:
        if n.graph_role == "procedural-parent":
            continue
        rel = n.rel
        owner = n.stem if n.directory == "axioms" else ""

        # node type validity
        if n.node_type and n.node_type not in NODE_TYPES:
            f.add("INVALID_NODE_TYPE", rel, f"node_type {n.node_type!r} not allowed", owner)
        expected = NODE_DIRS.get(n.directory)
        if n.node_type and expected and n.node_type != expected:
            f.add(
                "INVALID_NODE_TYPE",
                rel,
                f"node_type {n.node_type!r} contradicts directory {n.directory}/",
                owner,
            )

        # range fields: null members, empty lists, absent when required
        for key in RANGE_KEYS:
            if key not in n.meta:
                continue
            value = n.meta[key]
            if isinstance(value, list):
                if len(value) == 0:
                    f.add("MISSING_RANGE", rel, f"{key} is an empty list", owner)
                elif any(v is None or str(v).strip() in ("", "null") for v in value):
                    f.add("NULL_RANGE", rel, f"{key} contains a null member: {value!r}", owner)
                elif not parse_lines(value):
                    f.add("NULL_RANGE", rel, f"{key} has no parseable line numbers: {value!r}", owner)
            elif value is None:
                f.add("MISSING_RANGE", rel, f"{key} is null", owner)

        if n.directory == "axioms" and "source_content_ranges" not in n.meta:
            f.add("MISSING_RANGE", rel, "source_content_ranges absent entirely", owner)
        if n.directory != "axioms" and "source_support_ranges" not in n.meta:
            f.add("MISSING_RANGE", rel, "source_support_ranges absent entirely", owner)

        # title / filename / heading — strict, and punctuation tolerance called out
        title = n.title
        if title:
            if sanitize_filename(title) != n.stem:
                f.add("HEADING_MISMATCH", rel, f"title {title!r} does not encode to filename {n.stem!r}", owner)
            heading = n.heading
            if heading is None:
                f.add("HEADING_MISMATCH", rel, "no H1 heading", owner)
            elif heading != title:
                f.add("HEADING_MISMATCH", rel, f"H1 {heading!r} != title {title!r}", owner)

        # link resolution
        for target, _ in n.links():
            if resolve_link(target, index) is None:
                f.add("BROKEN_LINK", rel, f"[[{target}]] does not resolve", owner)

    # ---------------- child / parent relationship checks ----------------
    for c in children:
        targets, form = parent_targets(c)
        rel = c.rel

        if form == "absent" or not targets:
            f.add("PARENT_UNRESOLVED", rel, "parent_axiom missing or holds no wiki-link")
            continue
        if form == "space-joined":
            f.add(
                "PARENT_FORMAT",
                rel,
                f"{len(targets)} parents encoded as one space-joined string; the graph also "
                "uses a YAML list elsewhere — not machine-readable as a list",
            )
        elif form == "yaml-list" and len(targets) == 1:
            f.add("PARENT_FORMAT", rel, "single parent wrapped in a YAML list; inconsistent with single-value form")

        declared: set[str] = set()
        for t in targets:
            hit = resolve_link(t, index)
            if hit is None:
                f.add("PARENT_UNRESOLVED", rel, f"parent_axiom {t!r} does not resolve")
            else:
                declared.add(hit.stem)

        linking = links_to.get(rel, set())
        for missing in sorted(declared - linking):
            f.add(
                "PARENT_RECIPROCITY",
                rel,
                f"names parent {missing!r} but that router does not reach this node",
                missing,
            )
        for missing in sorted(linking - declared):
            f.add(
                "PARENT_RECIPROCITY",
                rel,
                f"router {missing!r} links this node but it is absent from parent_axiom",
                missing,
            )

        # support ranges must sit inside some declared parent's own ranges
        support = parse_lines(c.meta.get("source_support_ranges"))
        if support and declared:
            allowed: set[int] = set()
            for stem in declared:
                p = axioms.get(stem)
                if p is None:
                    continue
                allowed |= parse_lines(p.meta.get("source_content_ranges"))
                allowed |= parse_lines(p.meta.get("source_statement_lines"))
            outside = sorted(support - allowed)
            if allowed and outside:
                f.add(
                    "RANGE_CONTAINMENT",
                    rel,
                    f"cites source line(s) {outside} outside every declared parent's "
                    f"statement/content ranges",
                    ", ".join(sorted(declared)),
                )

    # ---------------- sub-line provenance detectability ----------------
    for n in nodes:
        if n.graph_role == "procedural-parent":
            continue
        raw = str(n.meta.get("detached_source_ranges", ""))
        if raw and re.search(r"[A-Za-z]", raw):
            f.add(
                "SUBLINE_UNREPRESENTABLE",
                n.rel,
                f"detached_source_ranges holds prose, not a numeric range: {raw!r}",
                n.stem if n.directory == "axioms" else "",
            )

    return f


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--csv", type=Path)
    args = ap.parse_args()

    root = args.root.resolve()
    findings = audit(root)
    rows = findings.rows

    by_code: dict[str, int] = defaultdict(int)
    affected: dict[str, set] = defaultdict(set)
    for r in rows:
        by_code[r["code"]] += 1
        affected[r["code"]].add(r["file"])

    print(f"AUDIT (read-only) {root}")
    print(f"{len(rows)} finding(s)\n")
    print(f"{'sev':<4} {'code':<26} {'count':>6}  files")
    for code in sorted(by_code, key=lambda c: (SEVERITY.get(c, 3), -by_code[c])):
        print(f"{SEVERITY.get(code,3):<4} {code:<26} {by_code[code]:>6}  {len(affected[code])}")

    if args.json:
        args.json.write_text(
            json.dumps({"root": str(root), "findings": rows}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["code", "severity", "file", "axiom", "detail"])
            w.writeheader()
            w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
