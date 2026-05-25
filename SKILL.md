---
name: document-naming
description: "Enforces the standard naming format across the content creation workspace."
version: "V4.3.0"
---

# Document Naming Convention

**Rule**: `Type_Title_YYYYMMDD_v1.0.0_Author.ext`

**Example**: `guide_origins-of-AI_20260523_v1.0.0_Kai.md`

---

## Prerequisites

Caller must determine:

| Prerequisite | Applies to | Description |
|-------------|------------|-------------|
| **operation type** | `create`, `modify`, `organize` | One of `create`, `modify`, or `organize` — inferred from user prompt. |
| **document type (default)** | `create` only | Suggested type prefix (e.g. `guide`, `plan`). Step 1 may override it. Not needed for `modify`/`organize`. |

---

## Configuration

All adjustable values live in **`config.json`**:

| Key | Default | Purpose |
|-----|---------|---------|
| `default_author` | `"Kai"` | Fallback author |
| `default_type` | `"other"` | Fallback type when Step 1 cannot resolve |
| `default_extension` | `"md"` | Fallback extension |
| `archive_dir_name` | `"history"` | Sub-directory for archived versions |
| `workspace_root` | `Desktop/content-creation-expert` | Primary workspace root |
| `workspace_config_path` | `"references/workspace.md"` | Relative path (from skill root) to workspace directory→type config document |
| `default_save_path` | Same as `workspace_root` | Fallback save location |

Scripts load `config.json` as a secondary fallback; the AI resolves values first.

---

## Step 1 — Type Matching

**Applies to: `create` and `organize`.**

Resolve the correct type prefix for the filename.  The resolved type
overrides the caller's default (create) or the current prefix (organize).

**Process:**

1. Read the workspace config document (path from config:
   `workspace_config_path`) to get the directory→type mapping.

2. Map the directory to its type (e.g. `04 articles/` → `article`).

3. Use the resulting type for this document.

**When workspace config is unreachable**, resolution falls back:

```
type resolution:
  preferred: workspace config document → directory-mapped type
  fallback: file's first-level parent directory matched against workspace config
  default: config.json → default_type ("other")
```

Directory→type mapping is defined in the workspace config (e.g. `04 articles/` → `article`).

**Save path:**

```
save path resolution (create):
  preferred: workspace config → target directory
  default: <default_save_path>/<document_type>/   (sub-directory created if missing)

save path resolution (organize):
  default: file's current directory (unchanged)
```

---

## Step 2 — File Generation

**Applies to: `create` and `modify`.**

Generates a compliant filename and writes the file to disk.  Uses the type from Step 1.

### Create — Generate Compliant Filename

**Field resolution:**

```
type resolution:
  preferred: Step 1 resolved type
  fallback: caller-provided document_type (default)
  default: config.json → default_type ("other")

title resolution:
  preferred: caller-provided title
  (script sanitisation: illegal chars stripped, ≤ 30 chars, spaces collapsed)
  default: "untitled"

date resolution:
  preferred: caller-provided --date override (YYYYMMDD)
  default: today (YYYYMMDD)

version resolution:
  default: always "v1.0.0" for new documents — hard-coded, no override

author resolution:
  preferred: context (SOUL.md / IDENTITY.md)
  fallback: config.json → default_author ("Kai")
  default: "Unknown"

extension resolution:
  preferred: caller-provided extension (leading dot stripped)
  default: config.json → default_extension ("md")
```

**Run the script:**

```bash
python scripts/naming.py generate "origins-of-AI" "md" \
    --type "guide" --author "Kai"
```

**Output:**

```json
{
  "name": "guide_origins-of-AI_20260523_v1.0.0_Kai.md",
  "type": "guide",
  "title": "origins-of-AI",
  "date": "20260523",
  "version": "v1.0.0",
  "author": "Kai",
  "ext": "md"
}
```

**Write the file:**

```bash
# Write content to the resolved save path from Step 1
cat > "<save_path>/guide_origins-of-AI_20260523_v1.0.0_Kai.md" << 'EOF'
<document content>
EOF
```

**Title sanitisation (applied by script):**
- Strips `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|` (illegal on Windows).
- Trims leading/trailing whitespace, collapses spaces (no separator).
- Truncates to **30 chars**.  Empty → `"untitled"`.

### Modify — Version Bump

Bumps the version and date from an existing compliant filename, then creates
a new file with modified content.  The old file is preserved for Step 4 archiving.

**Internal process:**

1. Parse filename against `^([^_]+)_(.+)_(\d{8})_v(\d+\.\d+\.\d+)_(\w+)\.(\w+)$`.
2. Increment version: `major` → X+1.0.0, `minor` → X.Y+1.0, `patch` → X.Y.Z+1.
3. Refresh date to today (`YYYYMMDD`).
4. Reconstruct new filename — replace old version and date; title, type, author, extension stay.

| Level | When to use | Version | Date |
|-------|-------------|---------|------|
| `major` | Full restructure | X+1.0.0 | today |
| `minor` | Content changes | X.Y+1.0 | today |
| `patch` | Format/typo fixes | X.Y.Z+1 | today |

**Run the script:**

```bash
python scripts/naming.py bump "guide_AI-guide_20260520_v1.0.0_Kai.md" minor
```

**Output:**

```json
{
  "old_name": "guide_AI-guide_20260520_v1.0.0_Kai.md",
  "new_name": "guide_AI-guide_20260523_v1.1.0_Kai.md",
  "old_version": "v1.0.0",
  "new_version": "v1.1.0"
}
```

**Create the new file and write modified content:**

```bash
cat > "<dir>/guide_AI-guide_20260523_v1.1.0_Kai.md" << 'EOF'
<modified document content>
EOF
```

---

## Step 3 — File Rename

**Applies to: `organize` only.**

Changes the type prefix of a compliant file using the type from Step 1.
All other fields stay.  Version and date are **never** changed — content
hasn't changed.

**Example:**

```
old: article_AI-guide_20260523_v1.0.0_Kai.md
new: guide_AI-guide_20260523_v1.0.0_Kai.md
     ^^^^^^ type changed, everything else preserved
```

Rename:

```bash
mv "article_AI-guide_20260523_v1.0.0_Kai.md" \
   "<dir>/guide_AI-guide_20260523_v1.0.0_Kai.md"
```

---

## Step 4 — File Archive

**Applies to: `modify` only.**

After Step 2 creates the new file, move the old file to the archive.

**Process:**

1. Verify source file exists.  Error if missing.
2. Create `<parent>/<archive_dir_name>/` (default `history`) if needed.
3. Move file into it.  On name collision, append `_1`, `_2`, …

**Run the script:**

```bash
python scripts/naming.py archive \
    "<dir>/guide_AI-guide_20260520_v1.0.0_Kai.md"
```

**Output:**

```json
{
  "archived": ".../guide_AI-guide_20260520_v1.0.0_Kai.md",
  "to": ".../history/guide_AI-guide_20260520_v1.0.0_Kai.md"
}
```

---

## CLI Commands

| Command | Usage | Step |
|---------|-------|------|
| `generate` | `naming.py generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD]` | Step 2 |
| `bump` | `naming.py bump <filename> <major\|minor\|patch>` | Step 2 |
| `archive` | `naming.py archive <file_path>` | Step 4 |

See Step 2 and Step 4 for detailed usage examples and output format.

---

## Python API

```python
from naming import (
    generate_name,       # Step 2 — new filename
    bump_version,        # Step 2 — version + date bump
    archive_old_version, # Step 4 — move to archive
    parse_filename,      # parse compliant filename → fields
)

# Create
result = generate_name("AI-guide", "md", file_type="guide", author="Kai")
# → {"name": "guide_AI-guide_20260523_v1.0.0_Kai.md", ...}

# Modify — bump
result = bump_version("guide_AI-guide_20260520_v1.0.0_Kai.md", "minor")
# → {"old_name": "...", "new_name": "guide_AI-guide_20260523_v1.1.0_Kai.md", ...}

# Archive
dest = archive_old_version("/path/to/guide_AI-guide_20260520_v1.0.0_Kai.md")
# → Path(".../history/guide_AI-guide_20260520_v1.0.0_Kai.md")

# Parse
fields = parse_filename("guide_AI-guide_20260523_v1.0.0_Kai.md")
# → {"type": "guide", "title": "AI-guide", "date": "20260523", ...}
```

---

## Edge Cases

| Case | Handling |
|------|----------|
| No type from caller (create) | Fallback to `default_type` from config (`"other"`) |
| No author from caller | Fallback chain: context → `default_author` → `"Unknown"` |
| Title longer than 30 chars | Truncated to 30 characters |
| Title contains illegal chars | `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|` are stripped |
| Title empty after sanitisation | Fallback to `"untitled"` |
| Workspace config unavailable (create) | Create `<default_save_path>/<type>/` sub-directory |
| Workspace config unavailable (organize) | Infer type from file's first-level parent directory under workspace root |
| Target filename already exists | Skip rename (no overwrite) |
| Archive collision | Append `_1`, `_2`, ... numeric suffix |
| Bump on non-compliant filename | Error — file must be compliant before bumping |
| Missing source file for archive | Error — file not found |
| Invalid bump type | Error — must be `major`, `minor`, or `patch` |
| Unknown CLI command | Error with usage help |
