# Step 2 — File Generation

**Applies to: `create` and `modify`.**

Generates a compliant filename, resolves the save path, and writes the file. Uses the type from Step 1. Full format spec: [rules.md](rules.md).

---

## Create

### Filename

| Field | Source |
|-------|--------|
| **type** | Step 1 resolved type |
| **title** | Caller-provided → sanitised (strip `\/:*?"<>|`, remove whitespace, ≤ 30 chars). Empty → error |
| **date** | Caller `--date` → today |
| **version** | `v1.0.0`. Append `.final` or `.refer` suffix if caller specifies |
| **author** | SOUL.md / IDENTITY.md → `config.json` `default_author` → `"Unknown"` |
| **extension** | Caller-provided → `config.json` `default_extension` → `.md` |

### Save Path

| Level | Rule |
|-------|------|
| **L1** | Type found in workspace config Directory→Type Mapping → use mapped directory. Type not found → `99 <fallback_dir_name>/` (default `"other"`) |
| **L2** | Follow workspace config Sub-directory Structure for the matched L1 directory. Create directory if missing |

### Write

Write the file to the resolved path.

---

## Modify

### Version Bump

| Step | Action |
|------|--------|
| **Parse** | Extract version segments from existing compliant filename |
| **Increment** | `major` → X+1.0.0 / `minor` → X.Y+1.0 / `patch` → X.Y.Z+1 |
| **Suffix** | Preserve existing `.final`/`.refer` suffix; override if caller specifies |
| **Date** | Set to today |
| **Reconstruct** | Only version, date, suffix change; title, type, author, extension stay |

### Write

New file written to the **same directory** as the original. Original file is archived by Step 3.
