# Workspace Management Rules

## Standard Format

```
Type_Title_YYYYMMDD_v1.0.0_Author.ext
```

Example: `guide_claw-content-strategy_20260407_v1.0.0_Kai.md`

---

## Prerequisites

The caller must provide:

| Prerequisite | Applies to | Description |
|-------------|------------|-------------|
| **operation type** | create, modify, organize | `create` / `modify` / `organize` — determined from the user's prompt |
| **document type** | create, organize | Type prefix provided by the caller. Step 1 resolves it against the workspace directory mapping. |

---

## Fields

| Field | Rule |
|-------|------|
| Type | Resolved through Step 1 chain: workspace config → directory-name match. **Error if no match found — no default applied.** |
| Title | ≤ 30 chars. `\/:*?"<>|` stripped. Spaces collapsed. **Error if empty after sanitisation.** |
| Date | `YYYYMMDD`. Today by default. Refreshed on modify. Preserved on organize |
| Version | Always `v1.0.0` for new documents |
| Author | Caller context (SOUL.md / IDENTITY.md) → config.json `default_author`. **Error if not configured.** |
| Extension | Caller-provided → config.json `default_extension`. **Error if not configured.** |

---

## Error Handling

This skill does NOT apply silent defaults. When a config value is missing or a resolution chain fails:
- Stop immediately.
- Report `ERROR: ...` with clear indication of what is missing.
- Prompt user to configure the relevant entry.

---

## 4-Step Workflow (Overview)

Full details for each step are in the separate reference files. This section is an overview only.

| Step | Applies to | Details in |
|------|-----------|-----------|
| Step 1 — Type Matching | create, organize | `references/step1-type-matching.md` |
| Step 2 — File Generation | create, modify | `references/step2-file-generation.md` |
| Step 3 — File Rename | organize | `references/step3-file-rename.md` |
| Step 4 — File Archive | modify | `references/step4-file-archive.md` |

---

## Version Policy

| Level | When |
|-------|------|
| `major` | Full restructure of topic / content / framework |
| `minor` | Content revisions — additions, deletions, changes |
| `patch` | Format fixes, grammar, typo corrections |

- **New documents**: always `v1.0.0`
- **Modify**: bump version + refresh date to today, create new file, write modified content
- **Organize**: version and date preserved (no bump, no refresh)

---

## CLI Commands

| Command | Usage |
|---------|-------|
| `generate` | `naming.py generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD]` |
| `bump` | `naming.py bump <filename> <major\|minor\|patch>` |
| `archive` | `naming.py archive <file_path>` |

---

## Python API

```python
from naming import (
    generate_name,       # Step 2 — compliant filename for new document
    bump_version,        # Step 2 — version bump + date refresh for modify
    archive_old_version, # Step 4 — move file to archive sub-directory
    parse_filename,      # parse compliant filename to dict or None
)
```

---

## Workspace Config Integration

This skill reads the workspace config document (path: `config.json` → `workspace_config_path`) for directory→type mapping in Step 1. The mapping is defined in `references/workspace.md`.

### Error Handling

- **Workspace config unavailable or path not configured** → stop, report `ERROR: workspace config document not found. Please configure "workspace_config_path" in config.json.`
- **Directory not in mapping** → stop, report `ERROR: directory "<dir>" is not listed in workspace config.`
- **Type has no matching directory (organize)** → stop, report `ERROR: no directory found for type "<type>".`
