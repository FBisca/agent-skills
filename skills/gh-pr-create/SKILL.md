---
name: gh-pr-create
description: Creates GitHub Pull Requests safely using `gh` CLI. Use when user wants to create a PR, open a pull request, submit for review, or push and open PR. Handles branch detection, target branch confirmation, body generation via temp file (avoids shell escaping issues), and label suggestion.
---

# GitHub PR Creation Skill

Creates Pull Requests reliably using `gh` CLI, avoiding common shell escaping pitfalls.

## When to Use

- User says "create a PR", "open a pull request", "push and create PR", "submit for review"
- After completing a feature, fix, or refactoring task

## Pre-Flight Checks

Before anything else, verify the environment:

```bash
gh auth status
git rev-parse --abbrev-ref HEAD
git status --short
```

- If `gh` is not authenticated, run `gh auth login` first.
- If working tree is dirty, ask the user whether to commit first.
- If on `main` or `develop`, STOP — you should be on a feature branch.

## Target Branch — ALWAYS ASK

**You MUST ask the user which branch to target.** Present the question like:

> Creating PR from `<current-branch>`. Which base branch should I target?
> - `main` (default for this repo)
> - `develop`
> - Other: ___

Do NOT assume the target branch. Wait for the user's answer before proceeding.

Common patterns (suggest but don't assume):
| Branch pattern | Likely target |
|---|---|
| `feat/*`, `fix/*`, `refactor/*` | `main` or `develop` |
| `hotfix/*` | `main` |
| `release/*` | `main` |

## Gather Context

Run these to understand what the PR contains:

```bash
# Commits in this branch vs target
git log <target>..HEAD --oneline

# Files changed
git diff <target> --stat

# Check if branch is pushed
git log --oneline origin/<current-branch>..HEAD 2>/dev/null
```

If the branch hasn't been pushed yet:

```bash
git push -u origin <current-branch>
```

## Generate PR Title

Use **Conventional Commits** format: `<type>(<scope>): <description>`

- **type**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `perf`
  - Pick the dominant type from the commits
- **scope**: the main module/area affected (kebab-case)
- **description**: imperative mood, lowercase, no period, max 72 chars

Examples:
- `feat(tenant-app): add onboarding phone step with country-code selector`
- `fix(api): handle empty response from pipeline endpoint`
- `refactor(ui): migrate Select component to CVA variants`

## Generate PR Body

Write the body content covering:

1. **What** — Brief summary of the change (2-3 sentences max)
2. **Changes** — Bullet list of key changes (files or features, not every line)
3. **Testing** — How it was validated (tests, manual checks)
4. **Notes** — Any reviewer-relevant context (optional)

Keep it concise. No need for screenshots unless UI-heavy.

## Create the PR — CRITICAL: Use a Temp File for Body

**NEVER pass the PR body inline.** Backticks, quotes, and special characters can
break shell parsing. Always write the body to a temp file first using split steps.

### Step 1: Create/reset body file (single command)

```bash
BODY_FILE="/tmp/pr-body.md"
: > "$BODY_FILE"
```

### Step 2: Write body in split commands (no heredoc)

Use one command per section to avoid stuck terminals in chat shells:

```bash
printf '%s\n' '## What' '' 'Brief summary here.' '' >> "$BODY_FILE"
printf '%s\n' '## Changes' '' '- Change 1' '- Change 2' '- Change 3' '' >> "$BODY_FILE"
printf '%s\n' '## Testing' '' '- All tests pass (`pnpm test` / `pytest`)' '- Typecheck clean' >> "$BODY_FILE"
```

Optional validation before PR creation:

```bash
cat "$BODY_FILE"
```

### Step 2: Create the PR using `--body-file`

```bash
gh pr create --title "<type>(<scope>): <description>" --body-file "$BODY_FILE" --base <target-branch>
```

### Step 3: Clean up and confirm

```bash
rm "$BODY_FILE"
gh pr view --web
```

## If PR Creation Fails

If `gh pr create` fails or the body is malformed:

1. **Do NOT retry with inline `--body`.** It will fail the same way.
2. Write/fix the body in `"$BODY_FILE"` using split `printf` commands
3. If the PR was created with a broken body, fix it:
   ```bash
  gh pr edit <number> --body-file "$BODY_FILE"
   ```

## Label Suggestions

Check available labels first:

```bash
gh label list
```

Suggest labels based on commit types:

| Commit type | Suggested labels |
|---|---|
| `feat` | `feature`, `enhancement` |
| `fix` | `bug`, `bugfix` |
| `refactor` | `refactoring`, `tech-debt` |
| `docs` | `documentation` |
| `ci` | `ci/cd` |

Only apply labels that exist in the repo. Use `--label` flag if labels are available.

## Complete Workflow Summary

1. `gh auth status` — verify auth
2. **Ask user for target branch** — never assume
3. `git log <target>..HEAD --oneline` — review commits
4. `git push -u origin <branch>` — push if needed
5. Create `BODY_FILE` and write body in split `printf` commands (no heredoc)
6. `gh pr create --title "..." --body-file "$BODY_FILE" --base <target>`
7. `rm "$BODY_FILE"` — clean up
8. `gh pr view --web` — open in browser for user

## Rules

- **ALWAYS** ask for the target branch before creating the PR
- **NEVER** pass body content inline via `--body` flag
- **ALWAYS** use `--body-file` with a temp file
- **NEVER** use heredoc in chat terminals for PR body creation
- **ALWAYS** write PR body in split terminal commands
- **ALWAYS** push the branch before creating the PR
- **NEVER** create a PR from `main` or `develop` directly
- **ALWAYS** show the generated title and body to the user for approval before creating
