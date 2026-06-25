---
name: document-naming
description: "Document naming, file generation, version management and archiving — covers type matching, filename generation, version bumping and old-version archiving. Triggers: modify, adjust, edit, create, generate, add, split, optimize, refine, output, and any other scenario involving document creation or modification. **Format validation: only file extensions listed in config `allowed_extensions` are accepted. If the requested extension is not in the whitelist, refuse execution — even if the skill was triggered.**"
version: "V1.1.0"
---

# Document Naming

Generates and manages compliant filenames. Full format spec: [rules.md](references/rules.md).

---

## Configuration

Three sources merged at startup (priority high→low). All sources soft-fail — never halt on missing config.

| Source               | File / Key                          | Provides                                                                                       |
| -------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Workspace file**   | `workspace_config_path`             | When `enable_workspace_path` is `true` (default): read this file first for workspace data      |
| **Local config**     | `config.local.json`                 | Same keys as `config.json`. Holds actual values; not synced to remote repo to prevent leakage. |
| **Skill config**     | `config.json`                       | Top-level keys + nested `workspace` dict; fallback when workspace file unavailable             |

Merge order: workspace file (if enabled & readable) → `config.local.json` → `config.json` → hard-coded defaults.

**Config keys**:

| Key                        | Level              | Fallback                                                          |
| -------------------------- | ------------------- | ----------------------------------------------------------------- |
| `default_author`           | top-level           | merged config → `"Unknown"`                                       |
| `default_extension`        | top-level           | merged config → `md` (no leading dot)                             |
| `allowed_extensions`       | top-level           | merged config → `["md", "pptx", "xlsx", "docx", "pdf", "png", "mp4", "mp3"]` (whitelist; no leading dots) |
| `enable_workspace_path`    | top-level           | `true` — when `false`, workspace file is not parsed; workspace dict values still used as fallback |
| `workspace_config_path`    | top-level           | `"references/workspace.md"` (default path)                        |
| `workspace_root`           | `workspace` dict    | workspace file → dict → Desktop                                    |
| `archive_dir_name`         | `workspace` dict    | workspace file → dict → `"history"`                               |
| `refer_dir_name`           | `workspace` dict    | workspace file → dict → `"refer"`                                 |
| `fallback_dir_name`        | `workspace` dict    | workspace file → dict → `"other"`                                 |
| `directory_tree`           | `workspace` dict    | workspace file → dict → `{}` (empty `{}` = no default tree; workspace file or config dict must provide entries) |

**`directory_tree` structure**:

```json
{
  "draft": {
    "name": "draft",
    "type": "draft",
    "sub": {
      "<topic>": {"name": "<topic>"}
    }
  },
  "material": {
    "name": "material",
    "type": "material",
    "sub": {
      "illustration": {"name": "illustration"},
      "ai-hot": {"name": "ai-hot"}
    }
  },
  "daily": {
    "name": "daily",
    "type": "daily",
    "sub": {}
  }
}
```

- `name`: directory name (also used as key)
- `type`: type prefix for filename (Step 1 type matching uses this column only)
- `sub`: nested dict of sub-directories; empty `{}` means no sub-dirs

---

## Mandatory Validation — `allowed_extensions`

Before any step executes, validate the requested file extension against the `allowed_extensions` whitelist (loaded from merged config). This is a **hard gate** — not a soft fallback.

**Rule**: If the file extension (no leading dot) is not in `allowed_extensions`, the skill **refuses execution immediately**, regardless of whether the skill was triggered. No filename is generated, no file is written, no archive is performed.

**Purpose**: Prevent the skill from processing file types it is not designed to handle (e.g., executable files, system files, or arbitrary binary formats), avoiding accidental naming collisions or mis-routed files.

**Customization**: Add or remove extensions in `config.local.json` → `allowed_extensions` to match your workspace needs. The whitelist is a flat list of strings without leading dots: `["md", "pptx", "docx"]`.

---

## 3-Step Workflow

| Step                         | Applies to         | Reference                                                       |
| ---------------------------- | ------------------ | --------------------------------------------------------------- |
| **Step 1 — Type Matching**   | `create`           | [step1-type-matching.md](references/step1-type-matching.md)     |
| **Step 2 — File Generation** | `create`, `modify` | [step2-file-generation.md](references/step2-file-generation.md) |
| **Step 3 — File Archive**    | `modify`           | [step3-file-archive.md](references/step3-file-archive.md) — **MUST use move (mv/Move-Item/shutil.move), NEVER copy** |

---

## Reference Documents

| Document                        | Content                                                        |
| ------------------------------- | -------------------------------------------------------------- |
| [rules.md](references/rules.md) | Naming format, field definitions, version policy               |
| [workspace.md](references/workspace.md) | Workspace root, directory→type mapping, sub-directory layout, runtime config |
| [step1-type-matching.md](references/step1-type-matching.md) | Step 1 — type prefix resolution |
| [step2-file-generation.md](references/step2-file-generation.md) | Step 2 — filename generation and save path |
| [step3-file-archive.md](references/step3-file-archive.md) | Step 3 — old version archive and suffix routing |
