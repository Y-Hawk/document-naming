# Step 2 — File Generation

**Applies to: `create` and `modify`.**

Generates a compliant filename and writes the file to disk. Uses the type from Step 1.

**Prerequisites**:
* All required config values must be present in `config.json`. If any is missing, **stop and report an error** — do not apply any default value silently.
  > `ERROR: missing config key "<key>" in config.json. Please configure it before proceeding.`

---

## Create — Generate Compliant Filename

### Field Resolution

| Field | Resolution Chain |
|-------|-----------------|
| **type** | `preferred:` Step 1 resolved type → `error:` not resolved → stop |
| **title** | `preferred:` caller-provided title (sanitised: illegal chars stripped, ≤ 30 chars, spaces collapsed) → `error:` empty after sanitisation → stop, report error |
| **date** | `preferred:` caller-provided `--date` override (YYYYMMDD) → `fallback:` today (YYYYMMDD) |
| **version** | Always `v1.0.0` — hard-coded, no override |
| **author** | `preferred:` context (SOUL.md / IDENTITY.md) → `fallback:` config.json → `default_author` → `error:` not configured → stop, report error |
| **extension** | `preferred:` caller-provided extension (leading dot stripped) → `fallback:` config.json → `default_extension` → `error:` not configured → stop, report error |

### Title Sanitisation (applied by script)

* Strips `\`, `/`, `:`, `*`, `?`, `"`, `<`, `>`, `|` (illegal on Windows)
* Trims leading/trailing whitespace, collapses spaces (no separator)
* Truncates to **30 chars**
* **If empty after sanitisation** → stop, report error (no "untitled" fallback)

### Run the Script

```bash
python scripts/naming.py generate "origins-of-AI" "md" \
    --type "guide" --author "Kai"
```

### Output

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

### Write the File

```bash
cat > "<save_path>/guide_origins-of-AI_20260523_v1.0.0_Kai.md" << 'EOF'
<document content>
EOF
```

---

## Modify — Version Bump

Bumps the version and date from an existing compliant filename, then creates a new file with modified content. The old file is preserved for Step 4 archiving.

### Internal Process

1. Parse filename against `^([^_]+)_(.+)_(\d{8})_v(\d+\.\d+\.\d+)_(\w+)\.(\w+)$`.
2. Increment version: `major` → X+1.0.0, `minor` → X.Y+1.0, `patch` → X.Y.Z+1.
3. Refresh date to today (`YYYYMMDD`).
4. Reconstruct new filename — replace old version and date; title, type, author, extension stay.

### Bump Levels

| Level | When to use | Version | Date |
|-------|-------------|---------|------|
| `major` | Full restructure of topic / content / framework | X+1.0.0 | today |
| `minor` | Content revisions — additions, deletions, changes | X.Y+1.0 | today |
| `patch` | Format fixes, grammar, typo corrections | X.Y.Z+1 | today |

### Run the Script

```bash
python scripts/naming.py bump "guide_AI-guide_20260520_v1.0.0_Kai.md" minor
```

### Output

```json
{
  "old_name": "guide_AI-guide_20260520_v1.0.0_Kai.md",
  "new_name": "guide_AI-guide_20260523_v1.1.0_Kai.md",
  "old_version": "v1.0.0",
  "new_version": "v1.1.0"
}
```

### Write the New File

```bash
cat > "<dir>/guide_AI-guide_20260523_v1.1.0_Kai.md" << 'EOF'
<modified document content>
EOF
```
