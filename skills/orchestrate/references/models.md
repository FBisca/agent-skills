# The driver's model table

## Model classes

Fallback class→model table for a backend column absent from `--models-file`. That file's `## Model classes` table (`~/.claude/CLAUDE.md`) takes precedence.

| Class | Pi |
|---|---|
| small | `minimax/MiniMax-M3.1-Flash` |
| medium | `minimax/MiniMax-M3.1-Flash` |
| large | `minimax/MiniMax-M3.1-Flash` |

The driver passes the Pi column's model to each Pi worker. Codex/Claude columns remain canonical in `~/.claude/CLAUDE.md`.
