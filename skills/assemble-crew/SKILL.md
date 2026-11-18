---
name: assemble-crew
description: "Designs the graph of specialists that solves a problem: nodes, the edges that route work between them, the shared state, and a verifier that can send the result back. Run only when the user types /assemble-crew."
disable-model-invocation: true
---

Design the smallest graph of specialists that solves the problem. Propose it, then wait for my go before starting the work or spawning anyone.

1. **Verb and done-state.** Restate the problem as what it does to someone or something, not what it is called. Name the done-state as a condition a verifier can check.
2. **Loop first.** One specialist looping against that verifier is a one-node graph; propose that unless the work forces a split: distinct specialties hand off, branches run in parallel and join, a step needs other tools or models, or one failure must stay contained. Each split names the force that earns it.
3. **Nodes.** One per real specialty, drawn from the field whose professionals do that verb for a living; with several nodes, at least one from a field far from the obvious. For each: its one job, the state it reads, the state it writes, its tools. Done when every node owns an output no other node produces.
4. **Edges and state.** Route the work: sequence, condition (on which state), fan-out, fan-in (joined on what). List the shared state's fields with the one node that writes each. Done when every node is reachable and every path ends at the verifier.
5. **Verifier.** A read-only node from an adversarial field (short seller, forensic accountant, attacker, opposing counsel) that checks the result against the done-state and holds authority to send it back along a named edge. Say what it attacks first and the most send-backs before it escalates to me.

Show the graph as a diagram, then one row per node. When it runs, each node does its field's work, not its field's voice.
