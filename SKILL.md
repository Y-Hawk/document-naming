---
name: document-naming
description: "Document naming, file generation, version management and archiving — covers type matching, filename generation, version bumping and old-version archiving. Triggers: modify, adjust, edit, create, generate, add, split. File types: .md | .pptx .ppt | .xlsx .xls .csv .tsv | .docx .doc .pdf .txt | .png .jpg .jpeg .gif .svg .webp | .mp4 .mov .avi .webm | .mp3 .wav .ogg .flac."
version: "V1.0.1"
---

# Document Naming

Generates and manages compliant filenames. Full format spec: [rules.md](references/rules.md).

---

## Configuration

Runtime values are merged from two sources at startup. Neither source failing will halt the skill.

| Source               | File                                | Provides                                                                                            |
| -------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Skill config**     | `config.json`                       | `default_author`, `default_extension`, `default_workspace_root`, `workspace_config_path`            |
| **Workspace config** | (path from `workspace_config_path`) | `workspace_root`, `archive_dir_name`, `refer_dir_name`, `fallback_dir_name`; directory→type mapping |

**Fallback chain** (all soft — never halt):

| Config Key          | Priority                                                      |
| ------------------- | ------------------------------------------------------------- |
| `workspace_root`    | caller-specified → Desktop → context/system-matched directory |
| `archive_dir_name`  | workspace config → `"history"`                                |
| `refer_dir_name`    | workspace config → `"refer"`                                  |
| `fallback_dir_name` | workspace config → `"other"`                                  |
| `default_author`    | `config.json` → `"Unknown"`                                   |
| `default_extension` | `config.json` → `.md` (silent)                                |

If either config file is unreadable, emit warning and continue with defaults. Scripts follow the same logic (`naming.py` → `_load_config`).

---

## 3-Step Workflow

| Step                         | Applies to         | Reference                                                       |
| ---------------------------- | ------------------ | --------------------------------------------------------------- |
| **Step 1 — Type Matching**   | `create`           | [step1-type-matching.md](references/step1-type-matching.md)     |
| **Step 2 — File Generation** | `create`, `modify` | [step2-file-generation.md](references/step2-file-generation.md) |
| **Step 3 — File Archive**    | `modify`           | [step3-file-archive.md](references/step3-file-archive.md)       |

---

## Reference Documents

| Document                        | Content                                                                                                                           |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [rules.md](references/rules.md) | Naming format, field definitions, version policy                                                                                  |
| Workspace config                | Workspace root, directory→type mapping, sub-directory structure, configuration. Path from `config.json` → `workspace_config_path` |

---

## CLI Commands

```bash
python scripts/naming.py generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD] [--suffix final|refer]
python scripts/naming.py bump <filename> <major|minor|patch>
python scripts/naming.py archive <file_path>
```

---

## Python API

```python
from naming import generate_name, bump_version, archive_old_version, parse_filename
```
