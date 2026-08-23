# Systems Thinking

**A navigable systems-thinking thought partner for working through complex system problems with human judgment.**

This repository transforms ideas derived from John Gall's *Systemantics: The Systems Bible, Third Edition* into an explorable network of systems wisdom. Its purpose is not merely to catalog axioms. It helps a person describe the system they face, notice dynamics they may have missed, test interpretations, and arrive at better questions and actions.

Start with **[SYSTEM THINKING](<SYSTEM THINKING.md>)**. It is the thought partner's procedural entry point: a guide for using the corpus in conversation with a real problem rather than treating it as an automatic diagnosis or a rule engine.

## What the thought partner does

It helps a human:

- describe the system, its purpose, boundaries, actors, and behavior;
- find axioms that might illuminate the situation without presuming they apply;
- consider competing explanations and consequences;
- move between abstract principles and concrete examples;
- turn insight into questions, experiments, and proportionate next actions;
- preserve uncertainty and human judgment instead of manufacturing certainty.

The linked corpus supplies the thought partner's memory. **SYSTEM THINKING** supplies its way of working with that memory.

## How the graph works

Each file is intended to stand alone as a semantic idea. Axiom files act as concise routers whose links form a readable sentence:

> [NAMES CREATE FRAMES](<axioms/NAMES CREATE FRAMES.md>), for example, [Calling Someone a Crook Creates Opposing Categories](<examples/Calling Someone a Crook Creates Opposing Categories.md>). Therefore, [Labels Can Preserve the Problems They Describe](<effects/Labels Can Preserve the Problems They Describe.md>), so [Examine the Frame Before Accepting the Category](<practices/Examine the Frame Before Accepting the Category.md>).

The graph has five node types:

- `axioms/` — exact, all-caps source statements and their semantic routers
- `explanations/` — interpretations of what an axiom means
- `effects/` — consequences and dynamics that follow from it
- `examples/` — concrete instances that make it visible
- `practices/` — useful actions or questions for applying the wisdom

Exact axiom titles are shown in all caps wherever possible. Supporting links use semantic titles as visible prose, so readers see the idea rather than internal path syntax.

## Scope and limits

This is a thought partner, not a substitute decision-maker. It can suggest questions, interpretations, examples, and practices; it does not establish that an axiom applies to a particular situation, issue prescriptions by itself, or remove the need to inspect the actual system. Supporting nodes are interpretive adaptations, not quotations unless explicitly identified as such.

The underlying source conversion carried this warning: it was produced with AI processing and may contain errors. Use the graph as a consulting aid, verify important claims against an authoritative edition, and keep human judgment in the loop.

## Provenance and rights

Every corpus node retains the SHA-256 fingerprint of the canonical converted source used during decomposition:

`3f383cf589b88c1690b8c2dd5c001b96a872165d5a8b040627bf89e16ce96fe1`

See [NOTICE.md](NOTICE.md) for attribution and rights information. This repository intentionally has no open-source license; publication does not grant permission to reuse copyrighted source material or adaptations beyond rights supplied by law or the relevant rights holder.

## Validation

The graph includes two complementary, standard-library-only checks:

```sh
python3 scripts/validate_graph.py --root . --corpus
python3 scripts/audit/audit_checks.py --root .
```

The first validates graph structure and metadata. The second independently checks known semantic-decomposition failure modes. Automated checks support review; they do not replace fresh semantic review.

The latest exhaustive review record is [the 2026-08-22 semantic audit ledger](reports/EXHAUSTIVE-SEMANTIC-AUDIT-LEDGER-2026-08-22.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing routers or nodes. The central standard is simple: a title must express the node's idea on its own, and a router must remain intelligible when read as ordinary prose composed primarily of those linked titles.
