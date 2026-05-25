# Document Naming Convention Rules

## Standard Format

```
Type_Title_YYYYMMDD_v1.0.0_Author.ext
```

Example: `plan_claw-content-strategy_20260407_v1.0.0_Kai.md`

## Prerequisites

The caller must provide:

| Prerequisite | Applies to | Description |
|-------------|------------|-------------|
| **operation type** | create, modify, organize | `create` / `modify` / `organize` — determined from the user's prompt |
| **document type (default)** | create only | Suggested type prefix (e.g. `guide`, `plan`).  This is a starting point — Step 1 may override it.  Not needed for modify or organize. |

## Fields

| Field | Rule |
|-------|------|
| Type | Resolved through Step 1 chain: workspace config → directory-name match → `"other"` |
| Title | ≤ 30 chars. `\/:*?"<>|` stripped. Spaces collapsed. Empty → `"untitled"` |
| Date | `YYYYMMDD`. Today by default. Refreshed on modify. Preserved on organize |
| Version | Always `v1.0.0` for new documents |
| Author | Caller context → `default_author` in config → `"Unknown"` |
| Extension | Always at end. Leading dots stripped automatically |

## 4-Step Workflow

### Step 1 — Type Matching (create + organize)

Resolve type by reading the workspace config document
(path from config: `workspace_config_path` → directory→type mapping).

When workspace config is unreachable, resolution falls back:

```
type resolution:
  preferred: workspace config document → directory-mapped type
  fallback: file's first-level parent directory matched against workspace config
  default: config.json → default_type ("other")
```

- Directory→type mapping is defined in the workspace config
  (e.g. `04 articles/` → type `article`).

Save path resolution:

```
save path resolution (create):
  preferred: workspace config → target directory
  default: <default_save_path>/<document_type>/   (sub-directory created if missing)

save path resolution (organize):
  default: file's current directory (unchanged)
```

- **create fallback**: when workspace config is unavailable, create a
  sub-directory named after the document type under the default save
  path, and place the file there.
- **organize**: file stays in its current location — only the type
  prefix changes.

### Step 2 — File Generation (create + modify)

Generates a compliant filename and writes the file to disk.

**Create — generate + write:** `naming.py generate "title" "ext" --type T --author A`

Field resolution chains:

```
type resolution:
  fallback: Step 1 resolved type
  fallback: caller-provided document_type (default)
  default: config.json → default_type ("other")

title resolution:
  fallback: caller-provided title (sanitised: illegal chars stripped, ≤ 30 chars)
  default: "untitled"

date resolution:
  fallback: --date override (YYYYMMDD)
  default: today (YYYYMMDD)

version resolution:
  default: always "v1.0.0" — hard-coded, no override

author resolution:
  fallback: context (SOUL.md / IDENTITY.md)
  fallback: config.json → default_author ("Kai")
  default: "Unknown"

extension resolution:
  fallback: caller-provided extension
  default: config.json → default_extension ("md")
```

Title sanitisation (applied by script):
- Strip `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
- Remove leading/trailing whitespace
- Collapse spaces (no separator)
- Truncate to 30 characters
- Empty → `"untitled"`

**Modify — bump:** `naming.py bump "filename" <major|minor|patch>`

1. Parse filename with regex `^([^_]+)_(.+)_(\d{8})_v(\d+\.\d+\.\d+)_(\w+)\.(\w+)$`
2. Increment version: major → X+1.0.0, minor → X.Y+1.0, patch → X.Y.Z+1
3. Refresh date to today
4. Reconstruct new filename — title, type, author, extension stay unchanged
5. Create new file at save path with new filename, write modified content

### Step 3 — File Rename (organize only)

Use the type resolved in Step 1.  Replace only the type prefix:

- Type prefix changed to the Step 1 resolved type
- Title, date, version, author, extension preserved
- Version never bumped, date never refreshed
- If new type equals existing type → no change

### Step 4 — File Archive (modify only)

```
naming.py archive <old_file_path>
```

1. Verify source file exists
2. Create archive sub-directory (`config.json` → `archive_dir_name`, default `"history"`)
3. Move file into archive directory
4. Handle collisions: append `_1`, `_2`, ... suffixes

## Version Policy

| Level | When |
|-------|------|
| `major` | Full restructure of topic / content / framework |
| `minor` | Content revisions — additions, deletions, changes |
| `patch` | Format fixes, grammar, typo corrections |

- **New documents**: always `v1.0.0`
- **Modify**: bump version + refresh date to today, create new file, write modified content
- **Organize**: version and date preserved (no bump, no refresh)

## CLI Commands

| Command | Usage |
|---------|-------|
| `generate` | `naming.py generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD]` |
| `bump` | `naming.py bump <filename> <major\|minor\|patch>` |
| `archive` | `naming.py archive <file_path>` |

## Python API

```python
from naming import (
    generate_name,       # Step 2 — compliant filename for new document
    bump_version,        # Step 2 — version bump + date refresh for modify
    archive_old_version, # Step 4 — move file to archive sub-directory
    parse_filename,      # parse compliant filename to dict or None
)
```

## Workspace Config Integration

This skill reads the workspace config document
(path: `config.json` → `workspace_config_path`, default `"../../SOUL.md"`)
for directory→type alignment in Step 1.

### Fallback — Create

When workspace config is unavailable, a type-named sub-directory
is created under the default save path:

```
<default_save_path>/<document_type>/
```

The directory is created if missing.

### Fallback — Organize

When workspace config is unavailable, the type is inferred from
the file's first-level parent directory name under the workspace root
(e.g. `04 articles/` → type `article`).
