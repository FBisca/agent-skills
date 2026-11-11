# Notice

This skill is copied from `plugins/core-skills/skills/process-business-writing` in https://github.com/aleberriz/agent-skills, commit `fe71f802022b31a82e13fec9eef0aab2c4344fdf`, licensed under the Apache License 2.0 (`Apache-2.0`; full text in `LICENSE`).

Modified for these agent skills, 2026-11-11: `SKILL.md` frontmatter gains `disable-model-invocation: true`, and `agents/openai.yaml` is added with `allow_implicit_invocation: false`, so the skill loads only when invoked; the description's escaped `\"good writing,\"` becomes `'good writing,'`, so every harness reads back the exact text the file holds. The upstream's `process-git` skill is not carried here; the three lines that named it now name this repository's `git-commit` and `gh-pr-create`. Its sibling `analytics-data-storytelling` is carried alongside, so that link resolves unchanged. The rest of `SKILL.md` and `references/` is unchanged.

Upstream carries no NOTICE file and no copyright header. Nothing further to carry over under Apache-2.0 §4(c).
