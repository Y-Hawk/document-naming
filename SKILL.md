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

### Extension Validation (Hard Gate)

Extension validation is a **hard gate** enforced by `naming.py` before any step: any extension not in `allowed_extensions` is refused (no filename, no write, no archive). Rule + whitelist → `references/rules.md` §Extension.

---

## Workspace Root Resolution (prerequisite)

The root directory MUST be determined before any save-path decision. Resolution is **4-step, config-first**:

1. **Configured root** — `workspace_root` in the merged config (config.local.json overrides config.json) is non-empty → use it (authoritative, highest). `source=config`.
2. **Explicit root provided** — config empty + `--root` / `--workspace-root` passed (user/AI explicit) → adopt it **and persist** into config.local.json (becomes the future config). `source=root`.
3. **Context-inferred root** — config empty + no explicit root + `--context-root` passed (AI inferred from session) → use it, **never persisted** (re-inferred each run). `source=context`.
4. **Fallback** — config empty + nothing provided → `<system user root>/DocumentSpace` (auto-created). `source=default`.

> A user-specified root is **lower priority than an existing config root** — it only takes effect (and persists) when the config root is empty. "User highest priority" applies to the **L1/L2 save-directory** choice (below), not to overriding an already-configured root.

---

## Core Workflow

```
Type Matching → File Generation → File Archive
                                    ↑
                            (modify only)
```

### Phase 1. Type Matching —— Resolve type prefix and language (3-tier)

Detect the document language from title/content. Resolve the type **prefix** through three tiers, in order:

1. **Config match (highest for type)** — read the `directory_tree` and match the document's title/content against the existing L1 `type` values. If a config type matches → use it.
2. **AI defines a new type** — if no config type matches (or the config tree is unreadable) → the AI autonomously defines a new type from the content, then creates it via `upsert` (persisted to config).
3. **Default type (fallback)** — if the AI also cannot define a type → use the skill's default type, **adapted to the document language**: Chinese → `其它`, English → `Other`. The default category is the `99 其它` entry in config (the filename prefix adapts; the directory stays `99 其它`).

Resolve the type against the `directory_tree` (its `type` values) for **every** document. The detected language governs the **title and content wording**, not the directory structure or the type prefix. Do not create parallel English-named L1 directories — reuse the existing L1 that matches the concept (e.g. an English article → `03 Article`, prefix `Article`). If a genuinely new concept appears, create it under the tree via `upsert`.

## Save Directory Resolution (premised on a determined root)

Once the root is determined (above), resolve the **save directory** through four steps:

1. **User explicitly specifies L1/L2** → highest priority; save there.
2. **User unspecified** → read the `directory_tree` and match by type:
   - L1 hit + L2 hit → save under that L2.
   - L1 hit + no suitable L2 → create the L2 from AI context under that L1, save there.
   - No L1 hit → create the L1 for the type, and create the L2 from AI context under it, save there.
3. Any newly created L1/L2 is **upserted into the config tree** (persisted) — see `naming.py upsert`.
4. The resolved `save_path` is returned by `naming.py generate` (it auto-upserts and reports `save_path`).

> "User highest priority" lives here: an explicit user save location overrides config matching. It does NOT override an already-configured **root** (see Root Resolution step 1).

### Phase 2. File Generation —— Build compliant filename

Load `references/file-generation.md`. Generate filename in format `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}`. For create: generate new. For modify: bump version (major/minor/patch) on existing.

### Phase 3. File Archive —— Archive old version

Load `references/file-archive.md`. Applies to `modify` only. Move old version to the archive sub-directory whose **name matches the document's language** (a Chinese-named file → the Chinese archive folder; an English-named file → `history/`; `.refer` → the Chinese refer folder or `refer/`). **MUST use move (mv/Move-Item/shutil.move), NEVER copy.**

### Flow Control

```
Phase 1 → Type resolved? → yes → Phase 2
              └── no  → auto-detect + confirm (or timeout) → create dir + keep the workspace tree in sync → Phase 2
                                       └── create? → run `references/self_checklist.md` → deliver
                                       └── modify? → Phase 3 → run `references/self_checklist.md` → deliver
```

---

## Auto-Detect Flow (L1 & L2)

When the caller does **not** provide a type, the skill infers it from the document's **content**, then creates the matching directory and keeps the workspace tree in sync.

### L1 (first-level directory)

1. **Read the document content** (title + body). Infer the most appropriate L1 category (e.g. `Plan` / `Article` / `Question Bank` / `Asset` / `Standard` / `Opinion`). If genuinely unclassifiable, fall back to the default type (`其它` for Chinese, `Other` for English).
2. **Prompt the user to confirm** the inferred type, or let them supply a different one:
   > "Based on the content, this document appears to belong to the 【Plan】 category. Once confirmed I will auto-create the L1 directory `NN Plan` and keep the tree in sync; if the type is wrong, tell me the correct one. (No confirmation within the timeout → auto-execute)"
3. **On confirmation** (or **timeout** with no response → auto-execute):
   - Create the L1 directory on disk (zero-padded `01` numbering, next sequential — see `references/workspace.md` §Directory Numbering Convention).
   - Auto-update the tree: `naming.py upsert --l1 <type>` writes the new entry into the tree and returns the directory key.
4. Proceed to Phase 2 using the resolved type as the filename prefix.

### L2 (second-level directory)

Same logic, one level deeper:

1. **Infer the L2 sub-category** from content within the resolved L1 (e.g. under `03 Article` → `WorkBuddy` / `AI's Past and Present` …).
2. **Prompt to confirm** (or supply a different L2); warn that confirmation auto-creates the L2 directory and keeps the tree in sync; timeout → auto-execute.
3. On confirmation/timeout: `naming.py upsert --l1 <l1type> --l2 <l2type>` creates the L2 with forced `01` numbering and writes it back. Create the directory on disk.
4. Use the L2 as the save location; the filename type prefix stays the L1 type.

> The `upsert` command is idempotent: if the directory already exists it returns the existing key without changes. Confirmation is purely about *creating a new* directory and *notifying* the user.

---

## Constraints

| # | Rule |
|---|------|
| 1 | Extension MUST be in `allowed_extensions` whitelist — hard gate, no exceptions |
| 2 | Archive uses MOVE, never COPY — prevents data loss from copy+delete patterns |
| 3 | Local override wins; all runtime tree writes go to the machine-local config only (the baseline config is never written by the script) |
| 4 | Filename format strictly follows `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}` |
| 5 | Version bump follows semver: major (breaking), minor (feature), patch (fix) |
| 6 | Type is resolved against the `directory_tree` for every document; the detected language governs title/content, **not** the directory structure or type prefix. Do not create parallel English-named L1 directories. |
| 7 | **Directory numbering (MANDATORY)**: any first-level or second-level directory the skill creates by default under the workspace MUST carry a zero-padded 2-digit numeric prefix starting from `01`, sequential by sibling. Reserved/auto dirs (the archive/refer folders — `history`/`refer` in English, or their Chinese equivalents — and the `99_` fallback) are exempt. `naming.py upsert` enforces this automatically. |
| 8 | **Auto-detect requires confirmation**: when no type is supplied, the skill must propose a type and let the user confirm/correct before creating a *new* directory. Timeout (no response) → auto-execute with the proposed type. |
| 9 | **Pass AI context as flags**: when invoking `naming.py`, supply the context the AI identified from its session — `--author <real author>`, `--root <explicit root>` (persisted when config empty), and `--context-root <inferred root>` (session-inferred, never persisted). Root resolution is 4-tier: config > explicit root > context root > fallback. The static config always wins over an explicit/context root for the **root** itself; user highest priority applies to the **L1/L2 save directory**. Never use these flags to override an explicit config value. |
| 10 | **User save location is highest priority**: if the user explicitly names an L1/L2 (or a specific path), it overrides config-tree matching. This does NOT override an already-configured root (root follows its own 4-tier chain). |
| 11 | **Per-invocation additive sync (no delete)**: on every call, if a root is configured (source ≠ `default`), the config tree is additively synced from disk — new on-disk L1/L2 dirs are added to config; config entries missing on disk are NEVER removed. Deletions are not auto-pruned. |

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
→ Prompt: "Seems to belong to 【Article】 category; confirm to create the directory under '03 Article' and keep the tree in sync?"
→ User confirms (or timeout)
→ upsert --l1 Article --l2 WorkBuddy  → ensures "01 WorkBuddy" exists, updates the tree
→ Phase 2: generate "Article_WorkBuddyShortcuts_20260718_v1.0.0_Hawk.md"
```

### Modify an existing document

```
User: "Update the naming spec doc"
→ Phase 1: type match from existing filename
→ Phase 2: bump version → v1.0.0 → v1.1.0
→ Phase 3: archive old version to the language-matched folder (the Chinese archive folder or `history/`)
→ Deliver: new filename + archive path
```

### User specifies the storage directory (highest priority)

```
User: "Save this plan under 06 Plan / WorkBuddy"
→ Save Directory Resolution: user explicit L1/L2 → highest → save there
→ Phase 1: type=Plan (matched to "06 Plan")
→ Phase 2: generate "Plan_…_20260718_v1.0.0_Hawk.md" into 06 Plan/WorkBuddy/
```

### No type, unclassifiable content → language-adapted default

```
User: "Name this random note" (no type, AI cannot classify)
→ Phase 1 tier 3: default type → Chinese "其它" / English "Other" (reuses 99 其它)
→ Phase 2: generate "其它_…_v1.0.0_Hawk.md" into 99 其它/
```

### Root not configured, user provides it → persisted

```
User: "Put everything in D:/MyDocs" (config has no workspace_root)
→ Root Resolution tier 2: --root D:/MyDocs → adopted AND written to config.local.json
→ subsequent calls use it as source=config
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
| `references/workspace.md` | Directory-tree **schema, type resolution & numbering convention** | Always |
| `references/file-generation.md` | Filename generation and save path | Phase 2 |
| `references/file-archive.md` | Old version archive and suffix routing | Phase 3 |
| `references/self_checklist.md` | Quality self-checklist (P0/P1/P2) | Before delivery |

---

## FAQ

**Q: What happens if the extension is not in the whitelist?**
Execution is refused immediately. The skill returns an error listing the allowed extensions. Adjust the `allowed_extensions` value in the configuration files.

**Q: How do I add a new document category?**
Just create a document and let the skill auto-detect the type, or tell it the type explicitly. On confirmation (or timeout) the skill creates the numbered L1/L2 directory and updates the tree automatically via `naming.py upsert`. You normally never edit the tree by hand.

**Q: The directory tree looks out of sync — what do I do?**
The skill keeps the tree in sync **automatically and additively** on every call: when a root is configured, any new L1/L2 folder on disk is added to the config tree (preserving its number); config entries that no longer exist on disk are never removed. You normally need no manual action. For an explicit one-off reconciliation, run `naming.py scan` (dry-run) / `naming.py scan --apply`; for a single new category use `naming.py upsert --l1 <type> [--l2 <type>]`. Hand-editing the config JSON is only for fixing parse errors.

> **The tree tracks the real folders additively.** Each call adds newly-found disk directories into `directory_tree`; it never prunes config entries. `naming.py scan --apply` is the explicit full mirror when you want to force it.
