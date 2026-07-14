---
name: document-naming
description: >
  Document naming, file generation, version management and archiving. Triggers: modify, adjust, edit, create, generate, add, split, optimize, refine, output, and any scenario involving document creation or modification. 触发词：修改文档、创建文档、生成文件、版本管理、文件归档。
  **Hard gate: only file extensions in `allowed_extensions` whitelist are accepted. Refuse execution for non-whitelisted extensions.**
agent_created: true
---

# Document Naming

Generates and manages compliant filenames through a 3-step workflow: type matching → file generation → archive. Full format spec: `references/01_rules.md`.

---

## Preconditions

### Triggers

Any document creation or modification: modify, adjust, edit, create, generate, add, split, optimize, refine, output.

### Input Requirements

Confirm target file path and operation type (create/modify) before executing.

### Configuration

Three config sources merged at startup (priority high→low):
- workspace file (if `enable_workspace_path` is true)
- `config.local.json` → `config.json` → hard-coded defaults

All sources soft-fail — never halt on missing config. See `references/02_workspace.md` for full config keys and `directory_tree` structure.

### Hard Gate: Extension Validation

Before any step, validate the requested extension against `allowed_extensions` whitelist. If not in whitelist → **refuse execution immediately**. No filename generated, no file written, no archive.

---

## Core Workflow

```
Type Matching → File Generation → File Archive
                                    ↑
                            (modify only)
```

### Phase 1. Type Matching —— Resolve type prefix

Load `references/03_step1-type-matching.md`. Match caller type against `directory_tree` type entries. No match → use `fallback_dir_name`. No type provided → use fallback.

### Phase 2. File Generation —— Build compliant filename

Load `references/04_step2-file-generation.md`. Generate filename in format `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}`. For create: generate new. For modify: bump version (major/minor/patch) on existing.

### Phase 3. File Archive —— Archive old version

Load `references/05_step3-file-archive.md`. Applies to `modify` only. Move old version to `archive_dir_name`. **MUST use move (mv/Move-Item/shutil.move), NEVER copy.**

### Flow Control

```
Phase 1 → Type found? → yes → Phase 2
              └── no → use fallback → Phase 2
                                       └── create? → deliver
                                       └── modify? → Phase 3 → deliver
```

---

## Constraints

| # | Rule |
|---|------|
| 1 | Extension MUST be in `allowed_extensions` whitelist — hard gate, no exceptions |
| 2 | Archive uses MOVE, never COPY — prevents data loss from copy+delete patterns |
| 3 | Config merge is soft-fail — missing config never halts execution |
| 4 | Filename format strictly follows `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}` |
| 5 | Version bump follows semver: major (breaking), minor (feature), patch (fix) |

---

## Examples

### Create a new document

```
User: "Create a spec doc about skill standards"
→ Phase 1: type=spec, not in directory_tree → kept as "spec"
→ Phase 2: generate "spec_skill-standards_20260714_v1.0.0_hawk.md"
→ Deliver: filename + save path
```

### Modify an existing document

```
User: "Update the naming spec doc"
→ Phase 1: type match from existing filename
→ Phase 2: bump version → v1.0.0 → v1.1.0
→ Phase 3: archive old version to history/
→ Deliver: new filename + archive path
```

---

## Output Specification

### Output Format

Return JSON with: name, type, title, date, version, author, ext, save_path, archive_path (if modified).

### Output Rules

1. Always return structured JSON, never plain text
2. Archive confirmation must include both old and new paths
3. Extension validation failure returns error with allowed list

---

## Reference Documents

| Document | Purpose | When to Load |
|----------|---------|-------------|
| `references/01_rules.md` | Naming format, field definitions, version policy | Always |
| `references/02_workspace.md` | Workspace root, directory→type mapping, runtime config | Always |
| `references/03_step1-type-matching.md` | Type prefix resolution | Phase 1 |
| `references/04_step2-file-generation.md` | Filename generation and save path | Phase 2 |
| `references/05_step3-file-archive.md` | Old version archive and suffix routing | Phase 3 |
| `references/99_self_checklist.md` | Quality self-checklist (P0/P1/P2) | Before delivery |

---

## FAQ

**Q: What happens if the extension is not in the whitelist?**
Execution is refused immediately. The skill returns an error listing the allowed extensions. Add extensions in `config.local.json` under `allowed_extensions`.

**Q: How do I change the workspace root?**
Set `workspace_root` in your workspace config file (default: `references/02_workspace.md`). The value is an absolute path.
