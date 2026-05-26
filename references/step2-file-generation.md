# Step 2 — File Generation

**Applies to: `create` and `modify`.**

Generates a compliant filename, resolves the save path, and writes the file. Uses the type from Step 1.

---

## Create — Filename

### Field Resolution

| Field | Resolution Chain |
|-------|-----------------|
| **type** | Step 1 resolved type. Not resolved → stop, report error |
| **title** | Caller-provided title → sanitise (strip `\ / : * ? " < > \|`, collapse whitespace, truncate to 30 chars). Empty after sanitisation → stop, report error |
| **date** | Caller `--date` override (YYYYMMDD) → today |
| **version** | `v1.0.0`. Append `.final` if caller says final/approved, `.refer` if reference/backup |
| **author** | SOUL.md / IDENTITY.md → config.json `default_author`. Not configured → stop, report error |
| **extension** | Caller-provided (leading dot stripped) → config.json `default_extension` → `.md` |

---

## Create — Save Path

### Level 1 Directory

| Case | Action |
|------|--------|
| Type matched a standard directory | Use mapped L1 path from workspace config |
| Type has no match | `99 <type>/`; create if missing |

### Level 2 Sub-Directory

Resolved from the workspace config document's sub-directory rules for the matched type.

If no sub-directory rule matches:
1. Auto-generate a meaningful L2 name from the document topic or content
2. Create it under the matched L1 directory
3. Append the new sub-directory entry to the workspace config document

---

## Create — Write

Write the generated filename to the resolved save path with the document content.

---

## Modify — Version Bump

Bump version and date from an existing compliant filename; create a **new file** with modified content in the same directory. The original file is preserved for archiving (Step 3).

### Process

1. Parse: `^([^_]+)_(.+)_(\d{8})_v(\d+\.\d+\.\d+)(\.(final|refer))?_(\w+)\.(\w+)$`
2. Increment: `major` → X+1.0.0 / `minor` → X.Y+1.0 / `patch` → X.Y.Z+1
3. Append `.final` or `.refer` suffix if caller specifies
4. Refresh date to today
5. Reconstruct — only version, date, suffix change; title, type, author, extension stay

### Write

New file written to the **same directory** as the original.
