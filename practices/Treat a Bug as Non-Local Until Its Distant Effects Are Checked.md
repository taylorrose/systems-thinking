---
title: "Treat a Bug as Non-Local Until Its Distant Effects Are Checked"
node_type: practice
parent_axiom: ["[[axioms/A BUG MAY BE PURELY LOCAL, BUT YOU AND I CAN NEVER KNOW THAT FOR SURE]]","[[axioms/ONE DOES NOT KNOW ALL THE EXPECTED EFFECTS OF KNOWN BUGS]]"]
source_document: "Systemantics: The Systems Bible, Third Edition — John Gall"
source_sha256: "3f383cf589b88c1690b8c2dd5c001b96a872165d5a8b040627bf89e16ce96fe1"
source_support_ranges: ["1055"]
---

# Treat a Bug as Non-Local Until Its Distant Effects Are Checked

When a discovered bug seems to demand only a quick hard-wire fix, resist the simplistic approach. Before patching, ask what else depends on the behaviour in question and what the correction itself will change downstream, then look for the answers under the operating conditions the system will actually meet rather than under test conditions alone.

Since locality can never be established with certainty, keep the fix reversible and keep watching the far parts of the system after it is applied.
