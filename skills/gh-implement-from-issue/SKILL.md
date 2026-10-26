---
name: gh-implement-from-issue
description: Implements a feature from a GitHub issue end-to-end. Use when user wants to implement an issue, work on an issue, build a feature from a GitHub issue, or says "implement issue #123". Reads the issue (and its parent if referenced), creates a branch, implements the feature, commits, pushes, and opens a PR using the gh-pr-create skill.
---

# Github Implement From Issue

Automates the full lifecycle of implementing a GitHub issue: read → branch → implement → commit → push → PR.

## When to Use

- User says "implement issue #123", "work on issue #45", "build the feature from issue #78"
- User wants to pick up a GitHub issue and deliver it as a PR

## Prerequisites

Verify before starting:

```bash
gh auth status          # GitHub CLI authenticated
git rev-parse --git-dir # Inside a git repo
git status --short      # Check for uncommitted changes
```

- If `gh` is not authenticated → `gh auth login`
- If not in a git repo → STOP and inform the user
- If there are uncommitted changes → ask the user whether to stash or commit them first

## Workflow

### 1. Get the Issue Number

If the user provided an issue number, use it directly.

If not, **ask the user**:

> Which GitHub issue should I implement? (e.g., `#123` or just `123`)

### 2. Read the Issue

```bash
gh issue view <issue_number> --json number,title,body,labels,assignees,milestone
```

Extract and display a summary:

> **Issue #\<number>**: \<title>
>
> \<first ~5 lines of body or a brief summary>

If the issue is not found, STOP and inform the user.

### 3. Detect Parent Issue

Scan the issue body for references to a parent issue. Look for these patterns (case-insensitive):

- `parent issue #123` or `Parent: #123`
- `part of #123`
- `relates to #123`
- `child of #123`
- `tracks #123` / `tracked by #123`
- A "Parent issue" section or field containing `#<number>`
- GitHub sub-issue syntax or task list references

If a parent issue number is found:

```bash
gh issue view <parent_issue_number> --json number,title,body,labels
```

Display:

> **Parent Issue #\<number>**: \<title>
>
> \<brief summary of parent body>

Use **both** the issue and the parent issue as context for the implementation.
The current issue describes the specific task; the parent provides broader context and requirements.

### 4. Create Feature Branch

Generate the branch name:

```
feat/issue-<number>-<slugified-title>
```

Slugify rules:
- Lowercase
- Replace spaces and special characters with hyphens
- Remove consecutive hyphens
- Truncate to keep total branch name under 60 characters

Check if branch already exists:

```bash
git branch --list "feat/issue-<number>-*"
```

- If branch exists locally → ask user: "Branch already exists. Switch to it, or create a new one?"
- If no conflict → create and switch:

```bash
git checkout -b <branch-name>
```

### 5. Implement the Feature

This is the core implementation phase. Follow these principles:

1. **Analyze the repository** — understand the project structure, conventions, and relevant existing code
2. **Read project guidelines** — check for AGENTS.md, CLAUDE.md, contributing guides, or equivalent
3. **Plan the changes** — use the todo list to break the issue into actionable implementation steps
4. **Implement incrementally** — make focused, minimal edits that satisfy the issue requirements
5. **Follow project conventions** — match existing patterns for file placement, naming, styling, testing
6. **Include tests** — if the project has tests, add or update tests for the new behavior
7. **Run quality gates** — execute whatever checks the project requires (lint, typecheck, test, format)

If the issue is ambiguous or underspecified, make reasonable assumptions and document them.
If the issue is too large for a single PR, implement the most critical slice and note what remains.

### 6. Validate

Run all applicable quality checks before committing. Detect the toolchain from project files:

| Indicator | Commands to run |
|---|---|
| `package.json` with pnpm/turbo | `pnpm run lint && pnpm run typecheck && pnpm run test` |
| `package.json` with npm | `npm run lint && npm test` |
| `pyproject.toml` / `Makefile` | `bash scripts/lint.sh && bash scripts/test.sh` (or `make lint test`) |
| `AGENTS.md` | Read it — it specifies the exact commands |

**All checks MUST pass before committing.** Fix any failures before proceeding.

### 7. Commit

Stage all changes and commit with a Conventional Commits message.

**Single issue (no parent):**

```
feat: implement issue #<number> - <issue_title>
```

**With parent issue:**

```
feat: implement issue #<number> (part of #<parent_number>) - <issue_title>
```

Use the appropriate type (`feat`, `fix`, `refactor`, etc.) based on the issue content.
If the implementation spans multiple types, use the dominant one.

```bash
git add -A
git commit -m "<message>"
```

### 8. Push

```bash
git push -u origin <branch-name>
```

### 9. Create Pull Request

**Invoke the `gh-pr-create` skill** to create the PR. Provide it with:

- **Title**: The issue title (or a refined version if clearer)
- **Body** must include:
  - Summary of what was implemented
  - Key changes (bullet list)
  - Issue reference: `Fixes #<issue_number>` (this auto-closes the issue on merge)
  - Parent reference (if applicable): `Part of #<parent_number>`
  - Testing notes
- **Target branch**: Ask the user (the `gh-pr-create` skill handles this)

**CRITICAL**: Follow the `gh-pr-create` skill's rules — write the body to a temp file, use `--body-file`, never inline.

### 10. Report Results

After completion, summarize:

> **Done!** Here's what was delivered:
>
> - **Issue**: #\<number> — \<title>
> - **Parent**: #\<parent_number> — \<parent_title> *(if applicable)*
> - **Branch**: `<branch-name>`
> - **PR**: \<PR URL>
> - **Changes**: \<brief summary of what was implemented>

## Error Handling

| Scenario | Action |
|---|---|
| Issue not found | STOP — inform user, ask to verify the issue number |
| Not in a git repo | STOP — inform user |
| Uncommitted changes | Ask user: stash, commit, or abort |
| Branch already exists | Ask user: switch to existing, or create new with suffix |
| Quality gates fail | Fix the failures, do NOT skip checks |
| Push rejected | Pull/rebase first, then retry push |
| `gh` not authenticated | Run `gh auth login` |

**Never perform destructive operations (force push, reset, delete branches) without asking.**

## Rules

- **ALWAYS** read the issue before starting implementation
- **ALWAYS** check for a parent issue for additional context
- **ALWAYS** create a feature branch — never commit to `main` or `develop` directly
- **ALWAYS** run quality gates before committing
- **ALWAYS** use the `gh-pr-create` skill for PR creation (never inline `--body`)
- **ALWAYS** include `Fixes #<number>` in the PR body to auto-close the issue
- **ASK** the user before any destructive or ambiguous operation
- **KEEP** changes minimal and focused on the issue scope
- **FOLLOW** existing project conventions — do not introduce new patterns unnecessarily
