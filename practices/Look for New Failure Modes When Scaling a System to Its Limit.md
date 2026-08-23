---
title: "Look for New Failure Modes When Scaling a System to Its Limit"
node_type: practice
parent_axiom: "[[axioms/THE UNIVERSE IS LIKE A VERY LARGE SYSTEM]]"
source_document: "Systemantics: The Systems Bible, Third Edition — John Gall"
source_sha256: "3f383cf589b88c1690b8c2dd5c001b96a872165d5a8b040627bf89e16ce96fe1"
source_support_ranges: ["390", "394-396"]
---

# Look for New Failure Modes When Scaling a System to Its Limit

When a design is pushed to the largest, fastest, or tallest version of itself, do not assume its failures will resemble the failures of the smaller version. Ask which quantities grow with the new size and what each one now governs that it did not govern before.

Test the assumptions that the design's purpose rests on: whether the enclosure still excludes what it was built to exclude, whether duplicated parts can still fail independently, and whether the system can still complete its work inside the time available. Treat an unfamiliar failure mode as a possibility introduced by the extra scale rather than assuming it is peculiar to one build.
