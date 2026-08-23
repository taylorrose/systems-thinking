---
title: "Inspect a New Design for Obvious Faults Before Building On It"
node_type: practice
parent_axiom: "[[axioms/PLAN TO SCRAP THE FIRST SYSTEM YOU WILL ANYWAY]]"
source_document: "Systemantics: The Systems Bible, Third Edition — John Gall"
source_sha256: "3f383cf589b88c1690b8c2dd5c001b96a872165d5a8b040627bf89e16ce96fe1"
source_support_ranges: ["1573", "1575", "1577"]
---

# Inspect a New Design for Obvious Faults Before Building On It

Before committing effort to a design, read it as a plain object rather than as an intention. State what the system is built to do, then check each part against that figure: what speed, load, duration, or volume is it actually rated for, and what happens to everything around it when that rating is exceeded.

Look especially at the components on which the stated purpose depends, and ask what is left of the purpose if one of them has to be sacrificed to save the rest. Faults found at this stage are found for the price of looking.
