# Case mode

A **case** is a run frozen by `agent-eval capture`: `<home>/cases/<slug>/`, where `<home>` is `$AGENT_EVALS_HOME` or
`~/.local/state/agent-evals`. The case is the whole evidence, and the judgment ends as a `label/2` that
`agent-eval add-label` accepts: every deduction traceable to a verbatim quote in the case.

Run `agent-eval` from PATH, else as `uv run --project <agent-runtime checkout> agent-eval`. Its
`add-label --help` is the `label/2` contract: field rules and a complete example.

1. **Read the case.** `manifest.json` lists the sessions (`id`, `role`, `parent`, `file`), the orchestrate files
   (`orchestrate.files[].file`) and the `git` range of `changes.patch`. Read a listed file with
   `gzip -dc <case>/<file>`. The **subject** is the session the user named, else the root session (`parent` null)
   whose work `changes.patch` holds. Done when every listed file that bears on a rubric's Assess criteria is read.
2. **Judge** under [`SKILL.md`](SKILL.md). Each judgment is a **finding**: `kind` `proven` (observed in the case),
   `risk` (possible, unobserved) or `strength`; a 1.0 dimension cites its `strength`. A dimension's `label` is its
   rubric's anchor label (`problematic`, `mostly_efficient`).
3. **Cite.** `file` as the manifest lists it (or `changes.patch`), `line` where the quote starts (1-based, decompressed),
   `quote` copied raw from that line. Transcripts are JSONL: quote the JSON-escaped text as it sits in the line
   (`\"`, `\n`, `’`), never the rendered message.
4. **Write the label** to a scratchpad file. `judge.rubric_sha256`:
   `cat rubrics/code-quality.md rubrics/test-value.md rubrics/efficiency.md rubrics/communication.md | shasum -a 256`
   beside this file; `judge.model`: your exact model id. `score` rounds **half up** on the exact decimal mean
   (`Decimal(...).quantize(Decimal("0.01"), ROUND_HALF_UP)`): float `round()` disagrees on some combinations and
   add-label refuses it.
5. **Store it:** `agent-eval add-label <slug> --kind agent-judge <file>`. Exit 2 names every failing field and the
   expected score or verdict; fix each and rerun. Done at exit 0. Exit 1 (no case, or a label already stored) ends the
   run: report it and leave the case as it is.
6. **Print** SKILL.md's output block filled from the stored label, then the label's path.
