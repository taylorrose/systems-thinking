---
title: "Ask What Capability a Bug Might Be Revealing Before Removing It"
node_type: practice
parent_axiom: "[[axioms/BUG OR BONANZA]]"
source_document: "Systemantics: The Systems Bible, Third Edition — John Gall"
source_sha256: "3f383cf589b88c1690b8c2dd5c001b96a872165d5a8b040627bf89e16ce96fe1"
source_support_ranges: ["1069-1075"]
---

# Ask What Capability a Bug Might Be Revealing Before Removing It

On meeting an anomaly, hold the disposal decision long enough to ask a second question about it. Describe the behaviour without the word “bug”: state what the system did, under what conditions, and reliably or not.

Then ask what that behaviour would be worth if it were a feature — what it makes possible, what it detects, what problem outside the present purpose it might answer. Remove it once the answer is nothing of interest, and keep a note of anomalies too repeatable to be accidents even when no use is yet apparent.
