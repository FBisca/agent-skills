# Work across repositories

Manual cross-repository runs only. The driver handles one `--repo`, plan, and worktree set. Runtime mechanics: `agent-runtime` tools.

- Use one plan ledger; assign each worker an exact checkout.
- Identify peers by native runtime/session IDs.
- Agree on interface schemas, examples, revision identifiers, and compatibility before dependent implementation.
- Send concise changes/questions through native messages; keep code in assigned checkouts.
- Unblock only after verifying dependencies in the consumer checkout/reachable service; `COMPLETE` alone proves no integration.
- Assign one owner to run the combined acceptance checks. Keep commits and product descriptions independent of plan numbering.
- Relay through the orchestrator when native cross-session messaging is unavailable; custom mailboxes and unverified shell-prompt messages are forbidden.
