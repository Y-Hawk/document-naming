# Document Naming

A standardized skill for document naming, file generation, version management, and archiving. Provides unified filename formats, automatic version bumping, and old-version archiving for content creation workspaces.

## Features

- 📝 **Unified naming format** — `Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext`, automatically cleans illegal characters and whitespace
- 🔄 **Semantic versioning** — `major/minor/patch` three-level bumping, optional `.final` (approved) and `.refer` (reference) suffixes
- 📦 **Auto archiving** — Old versions are automatically moved to `history/` or `refer/` subdirectories when a document is modified, with zero residue
- ⚙️ **Single config source** — all runtime config lives in SKILL.md (parsed by the script at startup); the directory tree lives in `references/workspace.md` and is auto-synced. No JSON config files.
- 🔧 **Skill invocation** — Trigger naming, version bumping, and archiving via natural-language prompts; no manual script execution needed

## Quick Start

> **Iron rule**: All operations involving document creation or modification must invoke this skill first. Never construct filenames manually, never skip the 3-step workflow, never skip the skill for any change — regardless of perceived size.
>
> **Format validation (hard gate)**: only whitelisted extensions are processed; others are refused. Rule → `references/rules.md` §Extension and `SKILL.md` → Constraints #1.

### 1. Installation

Download the repository zip file, then install via the agent's skill import feature.

### 2. Usage

#### Scheme 1: Explicit Info

User provides full parameters; the skill executes directly:

| Operation | Prompt Template | Example |
|-----------|----------------|---------|
| Create document | `Create {type} document: {title}` | `Create guide document: Content Strategy` |
| Modify document | `Modify {filename}, {bump_level}` | `Modify guide_Content-Strategy_..._v1.0.0_Hawk.md, minor` |
| Archive old version | `Archive {filename}` | `Archive guide_Content-Strategy_..._v1.0.0_Hawk.md` |

Bump level: `major` (restructure) / `minor` (add/remove) / `patch` (fix typo)

#### Scheme 2: Natural Language (AI Auto-Judgment)

User expresses intent only; AI infers type and bump level automatically:

| Operation | Prompt Template | Example |
|-----------|----------------|---------|
| Create document | `Create a document about {title}` | `Create a document about content strategy` |
| Modify document | `Modify {filename}` | `Modify content strategy document, rewrote half of it` |

**Type inference**: When no type is given, the skill auto-detects it from the document content and asks the user to confirm (timeout → auto-execute); if unclassifiable, falls back to `Other`.

**Bump inference**: Rewrite/restructure → `major` · Add/remove sections → `minor` · Fix typos/format → `patch`

> Archive is automatically triggered after modifying a document — no separate invocation needed.

---

> **Trigger words**: create, generate, modify, adjust, edit, optimize, split, archive, and any scenario involving document creation or modification.

## Project Details

### 1. Naming Format

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

Example: `guide_content-strategy_20260407_v1.0.0_Hawk.md`

Full field definitions, fallback rules and version policy → [references/rules.md](references/rules.md)

### 2. Workflow

| Stage | Applies to | Description | Reference |
|------|------------|-------------|-----------|
| **Type Matching** | `create` | Match type prefix from the directory tree (§Type Resolution in `references/workspace.md`; auto-detect if absent) | [type-matching.md](references/type-matching.md) |
| **File Generation** | `create` / `modify` | Generate compliant filename and write file | [file-generation.md](references/file-generation.md) |
| **File Archive** | `modify` | Move old version to `history/` or `refer/` | [file-archive.md](references/file-archive.md) |

### 3. Configuration

This skill has **no JSON config files** — all runtime configuration lives in the `## Configuration` table of `SKILL.md` (single source, parsed at startup by `naming.py`). Edit that table to change author, extension whitelist, archive dirs, workspace root, etc. The directory tree is the authoritative source in `references/workspace.md` and is auto-synced by `naming.py upsert`.

**Workspace root — 3-tier resolution**: `workspace_root` (config) → `## Workspace Root` in `references/workspace.md` (context) → `<system user root>/DocumentSpace` (default; a `DocumentSpace` folder is created under the OS user home first, never the bare Desktop/user-root). Full detail and the per-OS root table → `SKILL.md` → Workspace Root Resolution & System User Root Directories. Inspect the resolved root with `naming.py root`.

## Caveats

- All config lives in `SKILL.md` (`## Configuration`); no JSON files — edit that table to change settings.
- Root resolves config → context → default `<user-home>/DocumentSpace`; see `SKILL.md` → Workspace Root Resolution.
- Directory tree authoritative source: `references/workspace.md` (auto-synced); inspect/fix with `naming.py tree`.
- Title empty / all special chars → falls back to `"untitled"`.
- No type given → auto-detect from content + confirm (timeout → auto-execute); unclassifiable → `Other`.
- `.final` suffix → archiving not triggered on modify; old version stays.
- Extension not in whitelist → execution refused (hard gate).

## Directory Structure

```
document-naming/
├── SKILL.md                      # Skill control file (includes the Configuration single source)
├── README.md                     # English documentation (canonical)
├── LICENSE                       # MIT License
├── references/
│   ├── rules.md                     # Naming format specification
│   ├── overview.md                  # Skill overview & command reference
│   ├── type-matching.md             # Type matching (incl. content auto-detect)
│   ├── file-generation.md           # File generation and save path
│   ├── file-archive.md              # File archive
│   ├── workspace.md                 # Directory tree authoritative source (auto-synced)
│   └── self_checklist.md            # Quality self-checklist
└── scripts/
    └── naming.py                 # Naming utility script (parses SKILL.md + workspace.md)
```

> `scripts/__pycache__/` is excluded by `.gitignore`. This skill no longer contains any local config file.

## About the Author

A super full-stack developer focused on AI. For more AI content, follow:

<img src="./assets/qcode.jpg" title="" alt="WeChat" width="261">

## License

[MIT License](LICENSE)
