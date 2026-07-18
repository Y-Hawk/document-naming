---
name: document-naming
description: >
  Document naming, file generation, version management and archiving. Triggers: create, modify, generate, or any document creation/modification. 触发词：修改文档、创建文档、生成文件、版本管理、文件归档。
agent_created: true
---

# Document Naming

Generates and manages compliant filenames through a 3-step workflow: type matching → file generation → archive. Full format spec: `references/rules.md`.

---

## Preconditions

### Triggers

Any document creation or modification: modify, adjust, edit, create, generate, add, split, optimize, refine, output.

### Input Requirements

Confirm the target file path and operation type (create/modify) before executing.

### Configuration

The remaining runtime configuration lives in **this file** as the single source
of truth — there are no JSON config files. `scripts/naming.py` parses the table
below at startup. Workspace-level settings (root, archive/refer directory names)
live in `references/workspace.md` instead — see that file. Change a value here
and the script picks it up immediately.

| Key                 | Value                               | Description                                           |
| ------------------- | ----------------------------------- | ----------------------------------------------------- |
| `default_author`    | `Hawk`                              | Author used when caller provides none                 |
| `default_extension` | `md`                                | Extension used when caller provides none (no dot)     |
| `allowed_extensions`| `md,pptx,xlsx,docx,pdf,png,mp4,mp3` | Whitelist — hard gate, non-listed extensions refused  |

The directory tree itself is **not** in this file — it lives in
`references/workspace.md`, which the script reads and auto-updates. That file is
also the authoritative source for the **workspace root** (`## Workspace Root`)
and the **archive/refer directory names** (`## Workspace Config`). See it for the
schema, the numbering convention, and those settings.

> The directory tree mirrors the real (Chinese-named) folders on disk — each L1's `type` is that folder's name minus the numeric prefix. Keep the two in sync with `naming.py scan` (see FAQ).

### Workspace Root Resolution

Before composing any save path, resolve the absolute root under which all L1/L2
directories live. The root is defined in `references/workspace.md`
(`## Workspace Root` section) — that is its authoritative location. Resolution
order:

1. **Workspace doc** — the `## Workspace Root` path in `references/workspace.md`
   (normally the active content workspace). If set, use it directly.
2. **Default** — `<system user root>/DocumentSpace`. **Never the bare Desktop /
   user-root.** If reached, **first create the `DocumentSpace` directory under
   the system user root**, then proceed — this keeps generated docs from mixing
   with unrelated items.

`naming.py root` returns the resolved root plus its `source` (`context` /
`default`). Only the `default` tier ever creates a directory. (There is no
SKILL.md config override — set the root in `references/workspace.md`.)

### System User Root Directories

The default tier resolves the root as `<system user root>/DocumentSpace`. The "system user root" is the **OS user home directory**, which differs per platform. `naming.py` resolves it at runtime via `Path.home()`; the table below lists the supported roots explicitly.

| System  | System user root (Path.home()) | Default root (fallback)            |
| ------- | ------------------------------ | ---------------------------------- |
| Windows | `C:\Users\<username>`          | `C:\Users\<username>\DocumentSpace` |
| macOS   | `/Users/<username>`            | `/Users/<username>/DocumentSpace`   |
| Linux   | `/home/<username>`             | `/home/<username>/DocumentSpace`    |

> The default root is always `<system user root>/DocumentSpace`, computed by `naming.py` via `Path.home()` for the current OS (see `references/rules.md` for this rule). There is no SKILL.md override — to change the root, edit the `## Workspace Root` path in `references/workspace.md`.

### Extension Validation (Hard Gate)

Extension validation is a **hard gate** enforced by `naming.py` before any step: any extension not in `allowed_extensions` is refused (no filename, no write, no archive). Rule + whitelist → `references/rules.md` §Extension.

---

## Core Workflow

```
Type Matching → File Generation → File Archive
                                    ↑
                            (modify only)
```

### Phase 1. Type Matching —— Resolve type prefix and language

Detect the document language from title/content. Resolve the type prefix:

- **Caller provides a type** → normalize against `directory_tree` type entries (match → mapped prefix; no match → keep caller type).
- **No type provided** → **auto-detect from content** (see §Auto-Detect Flow below). Do NOT silently fall back to a fixed bucket.

Resolve the type against the `directory_tree` (its `type` values) for **every** document. The detected language governs the **title and content wording**, not the directory structure or the type prefix. Do not create parallel English-named L1 directories — reuse the existing L1 that matches the concept (e.g. an English article → `03 Article`, prefix `Article`). If a genuinely new concept appears, create it under the tree via `upsert`.

### Phase 2. File Generation —— Build compliant filename

Load `references/file-generation.md`. Generate filename in format `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}`. For create: generate new. For modify: bump version (major/minor/patch) on existing.

### Phase 3. File Archive —— Archive old version

Load `references/file-archive.md`. Applies to `modify` only. Move old version to `archive_dir_name`. **MUST use move (mv/Move-Item/shutil.move), NEVER copy.**

### Flow Control

```
Phase 1 → Type resolved? → yes → Phase 2
              └── no  → auto-detect + confirm (or timeout) → create dir + update workspace doc → Phase 2
                                       └── create? → run `references/self_checklist.md` → deliver
                                       └── modify? → Phase 3 → run `references/self_checklist.md` → deliver
```

---

## Auto-Detect Flow (L1 & L2)

When the caller does **not** provide a type, the skill infers it from the document's **content**, then creates the matching directory and keeps the workspace tree in sync.

### L1 (first-level directory)

1. **Read the document content** (title + body). Infer the most appropriate L1 category (e.g. `Plan` / `Article` / `Question Bank` / `Asset` / `Standard` / `Opinion`). If genuinely unclassifiable, propose `Other`.
2. **Prompt the user to confirm** the inferred type, or let them supply a different one:
   > "Based on the content, this document appears to belong to the 【Plan】 category. Once confirmed I will auto-create the L1 directory `NN Plan` and sync the workspace doc; if the type is wrong, tell me the correct one. (No confirmation within the timeout → auto-execute)"
3. **On confirmation** (or **timeout** with no response → auto-execute):
   - Create the L1 directory on disk (zero-padded `01` numbering, next sequential — see `references/workspace.md` §Directory Numbering Convention).
   - Auto-update the tree: `naming.py upsert --l1 <type>` writes the new entry into `references/workspace.md` and returns the directory key.
4. Proceed to Phase 2 using the resolved type as the filename prefix.

### L2 (second-level directory)

Same logic, one level deeper:

1. **Infer the L2 sub-category** from content within the resolved L1 (e.g. under `03 Article` → `WorkBuddy` / `AI's Past and Present` …).
2. **Prompt to confirm** (or supply a different L2); warn that confirmation auto-creates the L2 directory and updates the workspace doc; timeout → auto-execute.
3. On confirmation/timeout: `naming.py upsert --l1 <l1type> --l2 <l2type>` creates the L2 with forced `01` numbering and writes it back. Create the directory on disk.
4. Use the L2 as the save location; the filename type prefix stays the L1 type.

> The `upsert` command is idempotent: if the directory already exists it returns the existing key without changes. Confirmation is purely about *creating a new* directory and *notifying* the user.

---

## Constraints

| # | Rule |
|---|------|
| 1 | Extension MUST be in `allowed_extensions` whitelist — hard gate, no exceptions |
| 2 | Archive uses MOVE, never COPY — prevents data loss from copy+delete patterns |
| 3 | Config is the single source in SKILL.md — `naming.py` parses it; no JSON config files |
| 4 | Filename format strictly follows `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}` |
| 5 | Version bump follows semver: major (breaking), minor (feature), patch (fix) |
| 6 | Type is resolved against the `directory_tree` for every document; the detected language governs title/content, **not** the directory structure or type prefix. Do not create parallel English-named L1 directories. |
| 7 | **Directory numbering (MANDATORY)**: any first-level or second-level directory the skill creates by default under the workspace MUST carry a zero-padded 2-digit numeric prefix starting from `01`, sequential by sibling. Reserved/auto dirs (`history`, `refer`, and the `99_` fallback) are exempt. `naming.py upsert` enforces this automatically. |
| 8 | **Auto-detect requires confirmation**: when no type is supplied, the skill must propose a type and let the user confirm/correct before creating a *new* directory. Timeout (no response) → auto-execute with the proposed type. |

---

## Examples

### Create a new document (type provided)

```
User: "Create a plan doc: Content Strategy"
→ Phase 1: type=Plan → mapped to "01 Plan"
→ Phase 2: generate "Plan_ContentStrategy_20260718_v1.0.0_Hawk.md"
→ Deliver: filename + save path
```

### Create a new document (type auto-detected)

```
User: "Create a doc about WorkBuddy shortcuts"  (no type given)
→ Phase 1: infer type=Article (matches "03 Article" series)
→ Prompt: "Seems to belong to 【Article】 category; confirm to create the directory under '03 Article' and sync the workspace doc?"
→ User confirms (or timeout)
→ upsert --l1 Article --l2 WorkBuddy  → ensures "01 WorkBuddy" exists, updates workspace.md
→ Phase 2: generate "Article_WorkBuddyShortcuts_20260718_v1.0.0_Hawk.md"
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
|----------|---------|--------------|
| `references/rules.md` | Naming format, field definitions, version policy | Always |
| `references/workspace.md` | **Directory tree (authoritative, auto-updated)**, directory→type mapping, directory numbering convention | Always |
| `references/file-generation.md` | Filename generation and save path | Phase 2 |
| `references/file-archive.md` | Old version archive and suffix routing | Phase 3 |
| `references/self_checklist.md` | Quality self-checklist (P0/P1/P2) | Before delivery |

---

## FAQ

**Q: What happens if the extension is not in the whitelist?**
Execution is refused immediately. The skill returns an error listing the allowed extensions. Adjust the `allowed_extensions` value in the SKILL.md Configuration table.

**Q: How do I add a new document category?**
Just create a document and let the skill auto-detect the type, or tell it the type explicitly. On confirmation (or timeout) the skill creates the numbered L1/L2 directory and updates `references/workspace.md` automatically via `naming.py upsert`. You normally never edit the tree by hand.

**Q: Where is the configuration stored now?**
Author / extension / whitelist live in this SKILL.md `### Configuration` table (parsed by `naming.py` at startup, no JSON config files). Workspace-level settings — the root (`## Workspace Root`) and the archive/refer directory names (`## Workspace Config`) — live in `references/workspace.md`.

**Q: The workspace.md tree looks out of sync — what do I do?**
Run `naming.py scan` to preview a sync (dry-run, no writes). It mirrors the real root folders into the tree, applying the four sync rules: (1) preserve each directory's existing number; (2) add/update/remove tree entries to match the disk; (3) skip dot-prefixed dirs (`.obsidian`) and system/app-class dirs (`Excalidraw`); (4) only L1/L2 — L3+ is reported but never added. Run `naming.py scan --apply` to write the sync. For a single new category you can also use `naming.py upsert --l1 <type> [--l2 <type>]`. Hand-editing the JSON block is only for fixing parse errors.

> **The tree mirrors the real folders.** `references/workspace.md`'s `## Directory Tree` is rebuilt to match the actual (Chinese-named) folders on disk — the `type` field of each L1 equals that folder's name with the numeric prefix stripped. `naming.py scan` is the single way to keep the two in lock-step.
