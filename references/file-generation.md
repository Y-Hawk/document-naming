# File Generation
**Applies to: `create` and `modify`.**

---

## Prerequisite

**Merged config** = values parsed by `naming.py` by merging `config.json` (baseline) with `config.local.json` (per-machine override). The `directory_tree` and `workspace_root` live in the same JSON files.

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
| **L1** | Type found in `directory_tree` → mapped directory. Not found → auto-detect + confirm, then `naming.py upsert --l1 <type>` creates it with `01` numbering and writes to `config.local.json` |
| **L2** | Follow the matched L1 entry's `sub` field. If the requested sub does not exist → auto-detect + confirm, then `naming.py upsert --l1 <l1type> --l2 <l2type>` creates it (forced `01` numbering) and writes back |
| **Numbering (L1/L2)** | Any directory the skill **creates by default** MUST carry a zero-padded 2-digit numeric prefix starting from `01`, sequential by sibling. Reserved dirs (`history`/`refer` in English, or their Chinese equivalents, and the `99_*` fallback) are exempt. `upsert` enforces this automatically — see `references/workspace.md` §Directory Numbering Convention |

> The `upsert` command is idempotent: passing an existing type returns the existing directory key without changes. Use it both to create new directories and to guarantee the tree in `config.local.json` stays in sync.

---

## Modify

> **MANDATORY ORDER — archive the old version BEFORE writing the new one.**
> Never overwrite the original file in place. The existing old version MUST be
> moved (MOVED, not copied) into the language-matched archive folder **before**
> the new version is written. `naming.py generate` does this automatically: when
> it detects an existing file of the same document (same type/title/author/
> extension, a *different* version) in the target directory, it moves that old
> file to the archive folder and returns `archive_path`. If you are not using
> `generate`'s auto-archive, you MUST run the File Archive step (Phase 3) first,
> then write the new file.

### Step 0 — Detect existing old version
Check the resolved `save_path` (the directory the original lives in) for any
file matching the same document with a **different version**. If one is found,
this is a `modify` and the archive step is **mandatory** — do not fall through
to a plain create.

### Version Bump

| Step | Action |
|------|--------|
| **Parse** | Extract version segments from existing filename |
| **Increment** | `major` → X+1.0.0 / `minor` → X.Y+1.0 / `patch` → X.Y.Z+1 |
| **Suffix** | Preserve existing; override if caller specifies |
| **Date** | Refresh to today |
| **Reconstruct** | Only version, date, suffix change; title, type, author, extension stay |

### Step 1 — Archive old version (BEFORE write)
Move the existing old-version file to the language-matched archive folder
(`历史版本`/`history`, or `参考备份`/`refer` for `.refer`; `.final` stays in
place). This is done for you by `naming.py generate` (it returns
`archive_path`), or manually via `naming.py archive <old_file>` / Phase 3. The
new file must be written **only after** the old one has been moved.

### Step 2 — Write new version
Write the newly generated file to the **same directory** as the original (now
vacated by the moved old version).
