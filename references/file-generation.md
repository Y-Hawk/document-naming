# File Generation
**Applies to: `create` and `modify`.**

---

## Prerequisite

**Merged config** = values parsed by `naming.py` from the SKILL.md `## Configuration` table. The `directory_tree` is read from `references/workspace.md`.

**Hard gate (extension)**: any extension not in `allowed_extensions` is refused before any step. Rule + whitelist → `references/rules.md` §Extension.

---

## Create

### Filename

| Field | Source |
|-------|--------|
| **type** | Type Matching resolved type (L1 directory name with numeric prefix stripped) |
| **title** | Caller-provided → sanitised (strip `\/:*?"<>|`, remove whitespace, ≤ 30 chars). Empty after sanitisation → fallback `"untitled"` |
| **date** | Today (`YYYYMMDD`) |
| **version** | `v1.0.0`. Append `.final` / `.refer` if caller specifies |
| **author** | Caller-provided → merged config `default_author` → `"Unknown"` |
| **extension** | Caller-provided → merged config `default_extension` → `md` (no leading dot). Hard gate — must be in `allowed_extensions` (see `references/rules.md` §Extension) |

### Save Path

| Level | Rule |
|-------|------|
| **L1** | Type found in `directory_tree` → mapped directory. Not found → auto-detect + confirm, then `naming.py upsert --l1 <type>` creates it with `01` numbering and writes to `references/workspace.md` |
| **L2** | Follow the matched L1 entry's `sub` field. If the requested sub does not exist → auto-detect + confirm, then `naming.py upsert --l1 <l1type> --l2 <l2type>` creates it (forced `01` numbering) and writes back |
| **Numbering (L1/L2)** | Any directory the skill **creates by default** MUST carry a zero-padded 2-digit numeric prefix starting from `01`, sequential by sibling. Reserved dirs (`history`, `refer`, `99_*` fallback) are exempt. `upsert` enforces this automatically — see `references/workspace.md` §Directory Numbering Convention |

> The `upsert` command is idempotent: passing an existing type returns the existing directory key without changes. Use it both to create new directories and to guarantee the workspace doc stays in sync.

---

## Modify

### Version Bump

| Step | Action |
|------|--------|
| **Parse** | Extract version segments from existing filename |
| **Increment** | `major` → X+1.0.0 / `minor` → X.Y+1.0 / `patch` → X.Y.Z+1 |
| **Suffix** | Preserve existing; override if caller specifies |
| **Date** | Refresh to today |
| **Reconstruct** | Only version, date, suffix change; title, type, author, extension stay |

New file written to the **same directory** as the original. Old file archived by File Archive.
