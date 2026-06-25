# Step 2 — File Generation

**Applies to: `create` and `modify`.**

---

## Prerequisite

**Merged config** = the flattened dict returned by `naming.py` `_load_config()`. After flattening, all workspace keys (`workspace_root`, `directory_tree`, etc.) are top-level — never accessed via `config["workspace"]`.

**Mandatory validation (hard gate)**: The requested file extension must be in `allowed_extensions` from merged config. If not → refuse execution. This check is performed before Step 1 (see [step1-type-matching.md](step1-type-matching.md) Prerequisite).

---

## Create

### Filename

| Field | Source |
|-------|--------|
| **type** | Step 1 resolved type |
| **title** | Caller-provided → sanitised (strip `\/:*?"<>|`, remove whitespace, ≤ 30 chars). Empty after sanitisation → fallback `"untitled"` |
| **date** | Today (`YYYYMMDD`) |
| **version** | `v1.0.0`. Append `.final` / `.refer` if caller specifies |
| **author** | Caller-provided → merged config `default_author` → `"Unknown"` |
| **extension** | Caller-provided → merged config `default_extension` → `md` (no leading dot). **Must be in `allowed_extensions` whitelist — hard gate** |

### Save Path

| Level | Rule |
|-------|------|
| **L1** | Type found in `directory_tree` → mapped directory. Not found → `99_<fallback_dir_name>/` (hard-coded prefix `99_` ensures fallback dir sorts last alphabetically) |
| **L2** | Follow `directory_tree` entry's `sub` field. Create if missing |

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

New file written to the **same directory** as the original. Old file archived by Step 3.
