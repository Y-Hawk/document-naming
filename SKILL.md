---
name: workspace-management
description: "Daily workspace file management — covers workspace root and first-level directory management, sub-directory conventions, and file naming standards."
version: "V5.0.0"
---

# Workspace Management

**Rule**: `Type_Title_YYYYMMDD_v1.0.0_Author.ext`

**Example**: `guide_origins-of-AI_20260523_v1.0.0_Kai.md`

---

## Prerequisites

Caller must determine:

| Prerequisite | Applies to | Description |
|-------------|------------|-------------|
| **operation type** | `create`, `modify`, `organize` | One of `create`, `modify`, or `organize` — inferred from user prompt. |
| **document type** | `create`, `organize` | Type prefix provided by the caller. Step 1 resolves it against the workspace directory mapping. |

---

## Configuration

All values are read from **`config.json`** at runtime. If a required key is missing, stop and report an error. **Exception: extension** silently defaults to `.md`.

| Key | Purpose |
|-----|---------|
| `default_author` | Author name used when not available from context |
| `default_extension` | Extension used when caller does not provide one |
| `archive_dir_name` | Sub-directory name for archived versions |
| `workspace_config_path` | Relative path (from skill root) to the workspace config document — provides workspace root, directory→type mapping, and sub-directory structure |

**Scripts load `config.json` as a secondary fallback; the AI resolves values first. If a value cannot be resolved from any source, stop and report an error.**

---

## 4-Step Workflow

Each step's full details are in separate reference files — read only the step needed:

| Step | Applies to | Reference |
|------|-----------|-----------|
| **Step 1 — Type Matching** | `create`, `organize` | [step1-type-matching.md](references/step1-type-matching.md) |
| **Step 2 — File Generation** | `create`, `modify` | [step2-file-generation.md](references/step2-file-generation.md) |
| **Step 3 — File Rename** | `organize` | [step3-file-rename.md](references/step3-file-rename.md) |
| **Step 4 — File Archive** | `modify` | [step4-file-archive.md](references/step4-file-archive.md) |

---

## Reference Documents

| Document | Content |
|----------|---------|
| [workspace.md](references/workspace.md) | Workspace root, directory→type mapping, sub-directory structure |
| [rules.md](references/rules.md) | Naming format, field definitions, version policy |

---

## CLI Commands

| Command | Usage | Step |
|---------|-------|------|
| `generate` | `naming.py generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD]` | Step 2 |
| `bump` | `naming.py bump <filename> <major\|minor\|patch>` | Step 2 |
| `archive` | `naming.py archive <file_path>` | Step 4 |

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

## Error Handling Principle

**This skill does NOT apply silent defaults** (with two exceptions: **extension** silently defaults to `.md` when not configured; **type** keeps original/caller-provided type when no match found — no error reported). For all other required config values, directory mappings, or field resolutions:
1. Stop immediately.
2. Report a clear `ERROR:` message indicating what is missing.
3. Prompt the user to configure the relevant entry.
