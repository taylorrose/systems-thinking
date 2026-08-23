# Contributing

Changes should make the corpus more useful as a systems-thinking thought partner while preserving traceability to the source. The graph is its memory structure; the experience it supports is a reflective conversation with a human about a real system problem.

## Semantic decomposition standard

1. Preserve an axiom's exact all-caps wording and use it as the visible link text wherever practical.
2. Keep the axiom body a minimal semantic router. Let linked titles carry the substantive meaning.
3. Give every supporting node a title that states its idea and can stand alone in a short sentence. Do not use bucket labels such as “Definition,” “Example,” or “Takeaway.”
4. Separate distinct content by function:
   - an explanation interprets meaning;
   - an effect states a consequence or dynamic;
   - an example shows a concrete instance;
   - a practice states an action or useful question.
5. Use natural transitions such as “for example,” “therefore,” “but,” and “so” to make the router readable as prose.
6. Preserve the source's degree of certainty. Do not turn “may” into “will,” or a tendency into a universal mechanism.
7. Do not invent causal claims, intentions, or advice that the source passage cannot support.
8. Link recursively when a supporting node still contains multiple independently useful ideas.
9. Keep frontmatter provenance, parent relationships, and source ranges accurate and portable.

## Review procedure

Before proposing a change:

1. Read the axiom, every node reachable from its router, and the relevant source range.
2. Read the router aloud using the visible link titles. It should sound like concise natural prose.
3. Open every link and confirm that its body contains exactly the idea promised by its title.
4. Confirm examples, explanations, effects, and practices are classified by their role rather than their topic.
5. Run both validators:

```sh
python3 scripts/validate_graph.py --root . --corpus
python3 scripts/audit/audit_checks.py --root .
```

6. Perform a fresh semantic review after the checks pass. A zero-finding validator result is not an acceptance signal by itself.

When changing the corpus broadly, record the review scope, decisions, and evidence in a dated report under `reports/`.
