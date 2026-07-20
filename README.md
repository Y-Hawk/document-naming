# Document Naming

A standardized skill for document naming, file generation, version management, and archiving. Provides unified filename formats, automatic version bumping, and old-version archiving for content creation workspaces.

## Features

- 📝 **Unified naming format** — `Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext`, automatically cleans illegal characters and whitespace
- 🔄 **Semantic versioning** — `major/minor/patch` three-level bumping, optional `.final` (approved) and `.refer` (reference) suffixes
- 📦 **Auto archiving** — Old versions are automatically moved to a language-matched folder when a document is modified (a Chinese filename → the Chinese archive/refer folders; an English filename → `history/` / `refer/`), with zero residue
- ⚙️ **Split JSON config** — runtime config lives in two root-level files: `config.json` (baseline, may be remote-managed) and `config.local.json` (per-machine, git-ignored, key-level override). The directory tree and workspace root live here too; all runtime writes land only in `config.local.json`.
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

**Type inference**: When no type is given, the skill auto-detects it from the document content (title, then first ~200 chars of body) and asks the user to confirm (timeout → auto-execute); if unclassifiable, falls back to the language-adapted default type (`其它` for Chinese, `Other` for English).

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
| **Type Matching** | `create` | Match type prefix from the directory tree (§Type Resolution in `references/workspace.md`; auto-detect if absent) | [workspace.md](references/workspace.md) |
| **File Generation** | `create` / `modify` | Generate compliant filename and write file | [file-generation.md](references/file-generation.md) |
| **File Archive** | `modify` | Move old version to the language-matched folder (`history/`·`refer/` for English, the Chinese folders for Chinese) | [file-archive.md](references/file-archive.md) |

### 3. Configuration

Runtime configuration lives in **two root-level JSON files**, merged at startup by `naming.py`:

| File | Role | Git |
|------|------|-----|
| `config.json` | Baseline snapshot (may be remote-managed / shared). Holds `default_author`, `default_extension`, `allowed_extensions`, `workspace_root`, `directory_tree`. | tracked |
| `config.local.json` | Per-machine, key-level override. Receives **all** runtime writes (scan / upsert / root). | git-ignored |

Merge rule: `config.local.json` overrides `config.json` key-by-key. This keeps machine-specific settings (root, tree) local so a remote-managed `config.json` never clobbers them. Archive / refer folder names are **not** config keys — they are fixed language-matched rules.

**Workspace root — resolution (4-tier, config-first)**: merged `workspace_root` (config.local.json wins) → explicit `--root` / `--workspace-root` flag (adopted **and persisted** to config.local.json when config empty) → `--context-root` / `--context-workspace-root` (session-inferred, **never persisted**) → `<system user root>/DocumentSpace` (default, auto-created). The static config is always authoritative for the **root itself**; "user highest priority" applies only to the L1/L2 save-directory choice. Inspect with `naming.py root`. (Full rule + priority table → `references/rules.md` §Workspace Root Resolution — single source of truth.)

**Author — resolution (3-tier)**: merged `default_author` → AI-provided `--author` flag → `"Unknown"`. Config wins over the flag.

**Directory tree — per-invocation additive sync (no delete)**: the merged `directory_tree` (config.local.json wins) is authoritative. On every call, when a root is **configured** (source ≠ default), new numbered L1/L2 dirs found on disk are added to the tree (numbers preserved); config entries missing on disk are **never** removed. When the root is the fallback, no sync runs. Forced full mirror (add/update/remove) with `naming.py scan --apply`.

## CLI Command Reference

Every command wraps `scripts/naming.py` and prints JSON (`{"error": "..."}` on failure). Run from the skill root.

| Command | Purpose | Example |
|---------|---------|---------|
| `generate <title> <ext> --type <t> [--author <a>] [--date YYYYMMDD] [--suffix final\|refer] [--version X.Y.Z] [--l2 <subtype>] [--root <path>] [--context-root <path>]` | Resolve type (3-tier) + auto-upsert the L1 (and optional L2) into config, create the dirs on disk if missing, return `save_path`, and **auto-archive any existing old version** (moved to the language-matched folder, `archive_path` returned) when a same-document different-version file is present. On `modify`, chain `bump` → `generate --version` (constraint #12). `--root` persists when config empty; `--context-root` is session-inferred (never persisted); both are the AI context tier (config wins) | `naming.py generate "Content Strategy" md --type Plan --author Hawk --l2 WorkBuddy` / `naming.py generate "Content Strategy" md --type Plan --author Hawk --version 1.1.0 --l2 WorkBuddy` |
| `bump <filename> <major\|minor\|patch>` | Bump version and refresh the date | `naming.py bump "Plan_ContentStrategy_20260718_v1.0.0_Hawk.md" minor` |
| `archive <file_path>` | Move the old version to the language-matched folder (move, never copy) | `naming.py archive "Plan_ContentStrategy_20260718_v1.0.0_Hawk.md"` |
| `tree [--root <path>] [--context-root <path>]` | Print the parsed directory tree (JSON); runs the per-invocation additive sync first | `naming.py tree` |
| `root [--root <path>] [--context-root <path>]` | Resolve the workspace root (4-tier: config → explicit `--root` (persisted) → `--context-root` (not persisted) → default) | `naming.py root` / `naming.py root --root /path/to/ws` / `naming.py root --context-root /path/to/session` |
| `upsert --l1 <t> [--l2 <t>] [--root <path>]` | Ensure an L1/L2 directory exists (01-numbering), write it back to `config.local.json`. Runs the per-invocation additive sync first | `naming.py upsert --l1 Article --l2 WorkBuddy` |
| `scan [--apply] [--root <path>]` | Full mirror of L1/L2 dirs on disk into the tree (add/update/remove); dry-run by default, `--apply` writes. Distinct from the per-invocation **add-only** sync | `naming.py scan` / `naming.py scan --apply` |

> The `directory_tree` in the merged config is the category source of truth and is **additively** synced from disk on every call (new dirs added, never pruned). For a forced full reconciliation, run `naming.py scan` (dry-run) then `naming.py scan --apply`. All writes land in `config.local.json`.

## Caveats

- Config lives in `config.json` (baseline) + `config.local.json` (per-machine override, git-ignored); edit these to change settings. Runtime writes go only to `config.local.json`.
- Root resolves 4-tier: config → explicit `--root` (persisted to config.local.json) → `--context-root` (session-inferred, never persisted) → default `<user-home>/DocumentSpace`. Inspect with `naming.py root`.
- Directory tree lives in the merged config (`config.local.json` wins); on every call (when a root is configured) it is **additively** synced from disk — new dirs added, never pruned. Inspect with `naming.py tree`; forced full mirror with `naming.py scan --apply`.
- Archive / refer folder names are not configurable — an English filename uses `history/` / `refer/`; a Chinese filename uses the equivalent Chinese folders.
- Title empty / all special chars → falls back to `"untitled"`.
- No type given → auto-detect from content + confirm (timeout → auto-execute); unclassifiable → language-adapted default (`其它` for Chinese, `Other` for English), reusing the `99 其它` entry.
- `.final` suffix → archiving not triggered on modify; old version stays.
- Extension not in whitelist → execution refused (hard gate).

## Directory Structure

```
document-naming/
├── SKILL.md                      # Skill control file
├── README.md                     # English documentation (canonical)
├── LICENSE                       # MIT License
├── config.json                   # Config baseline (tracked; may be remote-managed)
├── config.local.json             # Per-machine config override (git-ignored; runtime writes land here)
├── .gitignore                    # Ignores config.local.json + __pycache__/
├── references/
│   ├── rules.md                     # Naming format specification
│   ├── file-generation.md           # File generation and save path
│   ├── file-archive.md              # File archive
│   ├── workspace.md                 # Directory tree schema / type resolution / numbering convention
│   └── self_checklist.md            # Quality self-checklist
└── scripts/
    └── naming.py                 # Naming utility script (merges config.json + config.local.json)
```

> `config.local.json` and `scripts/__pycache__/` are excluded by `.gitignore`.

## Version History

- **v1.0.0** (2026-07-20) — Skill consolidated: 4-tier workspace-root resolution (config → explicit `--root` persisted → `--context-root` session-inferred → `DocumentSpace` fallback), 3-tier type resolution (config match → AI define → language-adapted default `其它`/`Other`), per-invocation additive tree sync (no delete), dual JSON config (`config.json` baseline + `config.local.json` machine-local), and deterministic `bump → generate --version` modify chain with automatic old-version archiving (`generate` moves the prior same-document version before writing the new one, returning `archive_path`).

## License

[MIT License](LICENSE)
