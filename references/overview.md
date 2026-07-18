# Skill Overview & Command Reference

A quick orientation for the `document-naming` skill: what it does, when to use it, and the `naming.py` commands it wraps.

---

## What it does

Generates and manages compliant filenames through a 3-step workflow:

1. **Type Matching** — resolve the document's type prefix from the directory tree (`references/workspace.md`).
2. **File Generation** — build a compliant filename (full format spec → `references/rules.md`).
3. **File Archive** — on modify, move the old version to `history/` (or `refer/`).

All runtime config lives in `SKILL.md` (`### Configuration` table); the directory tree lives in `references/workspace.md`. No JSON config files.

## When to use

Any operation that creates or modifies a document: modify, adjust, edit, create, generate, add, split, optimize, refine, output. **Invoke this skill first** — never construct filenames by hand.

## Command reference (`scripts/naming.py`)

| Command | Purpose | Example |
|---------|---------|---------|
| `generate <title> <ext> --type <t> [--author <a>] [--date YYYYMMDD] [--suffix final\|refer]` | Build a new compliant filename (no disk I/O) | `naming.py generate "Content Strategy" md --type Plan --author Hawk` |
| `bump <filename> <major\|minor\|patch>` | Bump version + refresh date | `naming.py bump "Plan_ContentStrategy_20260718_v1.0.0_Hawk.md" minor` |
| `archive <file_path>` | Move old version to `history/`/`refer/` | `naming.py archive "Plan_ContentStrategy_20260718_v1.0.0_Hawk.md"` |
| `tree` | Print the parsed directory tree (JSON) | `naming.py tree` |
| `root` | Resolve the workspace root (config → context → default) | `naming.py root` |
| `upsert --l1 <t> [--l2 <t>]` | Ensure an L1/L2 directory exists (01-numbering) and write it back | `naming.py upsert --l1 Article --l2 WorkBuddy` |

All commands output JSON; errors return `{"error": "..."}`.

## See also

- `references/rules.md` — naming format & version policy
- `references/type-matching.md` — type resolution
- `references/file-generation.md` — filename generation & save path
- `references/file-archive.md` — archive & suffix routing
- `references/workspace.md` — directory tree (authoritative, auto-updated)
- `references/self_checklist.md` — quality self-checklist
