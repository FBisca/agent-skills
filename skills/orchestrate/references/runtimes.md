# Runtime and Herdr integration

Read this reference only for teammate panes, cross-repository work, or runtime compatibility questions.

## Claude and existing Herdmates

Herdmates hosts Claude's native team processes in Herdr panes. Claude owns task assignment, messaging, and shutdown. Use the existing plugin; do not install another tmux shim or reproduce its recorder, hooks, or team files.

The existing `claude()` function in `zsh/.zsh/aliases.zsh` routes Claude through Herdmates inside Herdr. Start a new lead from an available shell pane with:

```sh
claude
```

If that shell function is unavailable, use `herdmates teammux-launch` directly. Do not probe `herdmates teammux-launch --help`: the launcher can change runtime state before Claude sees the argument.

Do not start this launcher as a tool inside an active Claude or Codex conversation. It starts a lead; it does not attach the current agent. If an existing Claude lead lacks the shim, explain that visible teammates require a lead started through Herdmates. Do not restart or duplicate its work automatically.

When the lead is ready:

1. Verify the available native teammate tools and the `implementer` definition.
2. Assign exact checkouts and ownership. Ask Claude to spawn native implementer teammates.
3. Let Herdmates create their panes. Verify returned agent IDs and observed Herdr pane IDs; record the mapping in the task handoff.
4. Check the Herdr sidebar for recognized agents. A shell pane without an agent is not a visible teammate.
5. Use native task completion and messages as work evidence. Sidebar states are presentation signals only.

The plugin's optional sidebar rows use `state_icon`, `agent`, `state_text`, `$task`, and `$status`. Inspect the installed plugin's `docs/sidebar-rows.toml` before changing a layout. Preserve existing configuration and run Herdr's configuration check when a layout is changed. Installing the plugin alone does not prove its lead launcher or optional metadata rows are active.

Shutdown remains with Claude/Herdmates. Do not close panes by name, sweep other sessions, or replace the plugin's lifecycle. Native task/teammate tool schemas vary by version; do not assume obsolete `TeamCreate` or `TeamDelete` tools exist.

## Codex / MultiAgent V2

Use the live spawn, message, follow-up, wait, and inspection tools. Keep runtime IDs in the ledger. `task_name` is a label; it does not select the custom `implementer` role.

Prefer the configured Terra implementer with no full-history fork. If the tool omits role/model selection, report the runtime limitation. Do not silently use an expensive inherited model or change global feature flags to work around it. Resume an existing agent with the runtime's follow-up operation after checking its context and checkout.

No native Codex-subagent-to-Herdr attachment has been verified for this workflow. `codex resume` opens a session but is not proof of safe concurrent attachment to a live child. `herdr agent attach` targets an agent already hosted in a Herdr pane. Neither command proves that a hidden child can be moved into a pane.

Keep native Codex workers visible through Codex's own agent UI. If the user chooses separate interactive Codex workers in Herdr, treat that as a distinct execution mode with its own ownership and communication setup. Never run both modes for the same task. Herdmates 3.x targets Claude native teams; its old mixed Claude/Codex orchestration was removed.

## Deterministic pane inspection

`python3 <skill-dir>/scripts/orchestrate.py herdr --session <exact-name> --pane <returned-id>` reads structured pane evidence. It requires a Herdr-managed caller and an explicit session. If injected identity is incomplete, do not fall back to whichever session has focus. Obtain the exact session identity from the launcher or user.

This helper does not create or close panes, attach threads, or claim that a pane belongs to a runtime agent. Verify the live registration against the native agent ID before recording a mapping. Pane labels and sidebar positions are not identifiers. If identity changes or becomes unreadable, preserve the worker and report the ambiguity.

## Work across repositories

- Keep one orchestration ledger for the active plan and one exact checkout assignment per worker.
- Identify peers by their native runtime/session IDs, not repository names alone.
- Agree on interface schemas, examples, revision identifiers, and compatibility before dependent implementation.
- Send concise changes and questions to assigned peers. Native messages carry text; code remains in the assigned checkouts.
- Verify that a dependency exists in its consumer's checkout or reachable test service before unblocking it. A ledger's `COMPLETE` status does not prove integration.
- Assign one owner to run the combined acceptance checks. Keep commits and product descriptions independent of plan numbering.
- If cross-session messaging is unavailable, relay through the orchestrator. Do not create a custom mailbox transport or type unverified messages into shell prompts.

## Sources and verification boundary

Reviewed against installed Herdr 0.8.2, Herdmates 3.2.0, Claude Code 2.1.263, and Codex CLI 0.153.4 on 2026-09-07. These are inspection versions, not universal minimum versions or proof of a live spawn test.

- [Herdmates](https://github.com/caioniehues/herdmates): native Claude panes, launcher, sidebar, lifecycle ownership.
- [Firstmate Herdr backend](https://github.com/kunchenguid/firstmate/blob/main/docs/herdr-backend.md): explicit session/endpoint identity and focus preservation. Use its design lessons; do not adopt its worktree or supervision framework implicitly.
- [Claude subagents](https://code.claude.com/docs/en/sub-agents): resumption, child context, compaction.
- [Claude Agent Teams](https://code.claude.com/docs/en/agent-teams) and [cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging).
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra).
