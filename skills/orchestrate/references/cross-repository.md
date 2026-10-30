# Work across repositories

Read this reference only for cross-repository execution. Runtime mechanics live in the `agent-runtime` tools.

- Keep one orchestration ledger for the active plan and one exact checkout assignment per worker.
- Identify peers by their native runtime/session IDs, not repository names alone.
- Agree on interface schemas, examples, revision identifiers, and compatibility before dependent implementation.
- Send concise changes and questions to assigned peers. Native messages carry text; code remains in the assigned checkouts.
- Verify that a dependency exists in its consumer's checkout or reachable test service before unblocking it. A ledger's `COMPLETE` status does not prove integration.
- Assign one owner to run the combined acceptance checks. Keep commits and product descriptions independent of plan numbering.
- If cross-session messaging is unavailable, relay through the orchestrator. Do not create a custom mailbox transport or type unverified messages into shell prompts.
