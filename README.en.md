# Document Naming

A standardized skill for document naming, file generation, version management, and archiving. Provides unified filename formats, automatic version bumping, and old-version archiving for content creation workspaces.

> **中文文档**: [README.md](README.md)

## Features

- 📝 **Unified naming format** — `Type_Title_YYYYMMDD_v<major.minor.patch>[_suffix]_Author.ext`, automatically cleans illegal characters and whitespace
- 🔄 **Semantic versioning** — `major/minor/patch` three-level bumping, optional `.final` (approved) and `.refer` (reference) suffixes
- 📦 **Auto archiving** — Old versions are automatically moved to `history/` or `refer/` subdirectories when a document is modified, with zero residue
- ⚙️ **Config-driven** — Multi-source merging, fully soft-fallback — never halts due to missing configuration
- 🔧 **Skill invocation** — Trigger naming, version bumping, and archiving via natural-language prompts; no manual script execution needed

## Quick Start

> **Iron rule**: All operations involving document creation or modification must invoke this skill first. Never construct filenames manually, never skip the 3-step workflow, never skip the skill for any change — regardless of perceived size.
>
> **Format validation (hard gate)**: only file extensions in the `allowed_extensions` whitelist are processed; extensions not in the whitelist are refused — even if the skill was triggered.

### Scheme 1: Explicit Info

User provides full parameters; the skill executes directly:

| Operation | Prompt Template | Example |
|-----------|----------------|---------|
| Create document | `Create {type} document: {title}` | `Create guide document: Content Strategy` |
| Modify document | `Modify {filename}, {bump_level}` | `Modify guide_Content-Strategy_..._v1.0.0_Hawk.md, minor` |
| Archive old version | `Archive {filename}` | `Archive guide_Content-Strategy_..._v1.0.0_Hawk.md` |

Bump level: `major` (restructure) / `minor` (add/remove) / `patch` (fix typo)

### Scheme 2: Natural Language (AI Auto-Judgment)

User expresses intent only; AI infers type and bump level automatically:

| Operation | Prompt Template | Example |
|-----------|----------------|---------|
| Create document | `Create a document about {title}` | `Create a document about content strategy` |
| Modify document | `Modify {filename}` | `Modify content strategy document, rewrote half of it` |

**Type inference**: Matches against workspace config's Directory→Type mapping → if no match, use `fallback_dir_name` (default `other`)

**Bump inference**: Rewrite/restructure → `major` · Add/remove sections → `minor` · Fix typos/format → `patch`

> Archive is automatically triggered after modifying a document — no separate invocation needed.

---

> **Trigger words**: create, generate, modify, adjust, edit, optimize, split, archive, and any scenario involving document creation or modification.

## Naming Format

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

Example: `guide_content-strategy_20260407_v1.0.0_Hawk.md`

Full field definitions, fallback rules and version policy → [references/rules.md](references/rules.md)

## 3-Step Workflow

| Step | Applies to | Description | Reference |
|------|------------|-------------|-----------|
| **Step 1** — Type Matching | `create` | Match type prefix from Directory→Type mapping | [step1-type-matching.md](references/step1-type-matching.md) |
| **Step 2** — File Generation | `create` / `modify` | Generate compliant filename and write file | [step2-file-generation.md](references/step2-file-generation.md) |
| **Step 3** — File Archive | `modify` | Move old version to `history/` or `refer/` | [step3-file-archive.md](references/step3-file-archive.md) |

## Configuration

Merge order: workspace config file (if `enable_workspace_path=true` & readable) → `config.local.json` → `config.json` → hard-coded defaults. All soft-fallback.

Full config keys, levels and fallback chains → [SKILL.md Configuration](SKILL.md)

### Directory & Type — Two Configuration Modes

Directory→type mapping (`directory_tree`) supports two modes, with read priority: workspace file > config dict.

**Mode 1: Workspace File**

Define Directory→Type Mapping and Sub-directory Structure in `references/workspace.md` using tables. This is just a reference document — as long as the format stays consistent, you can relocate it anywhere. Just set the file path in `workspace_config_path` and ensure `enable_workspace_path=true`; the script will automatically parse the file to generate `directory_tree`, overriding config dict values.

***Note: The configuration and directory tables in the document must maintain format consistency with that document. Sub-directories are optional.***

**Mode 2: Config Dict**

Configure directly in `config.json` / `config.local.json` under `workspace.directory_tree`:

```json
{
  "draft": {"name": "draft", "type": "draft", "sub": {"<topic>": {"name": "<topic>"}}},
  "material": {"name": "material", "type": "material", "sub": {"illustration": {"name": "illustration"}, "ai-hot": {"name": "ai-hot"}}},
  "daily": {"name": "daily", "type": "daily", "sub": {}}
}
```

- `name`: directory name (also used as dict key)
- `type`: filename type prefix (Step 1 uses only this field for type matching)
- `sub`: nested dict of sub-directories; `{}` means no sub-dirs

> **Choosing a mode**: Workspace file mode is easier for manual editing and reading; config dict mode suits automation or pure JSON environments. Both can coexist — workspace file overrides config dict when enabled, config dict is the fallback when disabled.

> **Config tip**: You can put personal values (author name, workspace path, etc.) directly in `config.json`. If you plan to push the repo to a remote (GitHub/Gitee etc.), copy `config.json` as `config.local.json`, move personal values there, and restore `config.json` to its empty-value template — this prevents local config from leaking to the remote repository.

## Directory Structure

```
document-naming/
├── SKILL.md                      # Skill control file
├── config.json                   # Default config template
├── README.md                     # Chinese documentation
├── README.en.md                  # English documentation
├── LICENSE                       # MIT License
├── references/
│   ├── rules.md                  # Naming format specification
│   ├── step1-type-matching.md    # Step 1 type matching
│   ├── step2-file-generation.md  # Step 2 file generation
│   ├── step3-file-archive.md     # Step 3 file archive
│   └── workspace.md              # Workspace config reference
└── scripts/
    └── naming.py                 # Naming utility script
```

> `config.local.json` and `scripts/__pycache__/` are excluded by `.gitignore` and do not appear in the remote repository.

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## License

[MIT License](LICENSE)
