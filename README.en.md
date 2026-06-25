# Document Naming

A standardized tool for document naming, file generation, version management, and archiving. Provides unified filename formats, automatic version bumping, and old-version archiving for content creation workspaces.

> **中文文档**: [README.md](README.md)

## Features

- 📝 **Unified naming format** — `Type_Title_YYYYMMDD_v<major.minor.patch>[_suffix]_Author.ext`, automatically cleans illegal characters and whitespace
- 🔄 **Semantic versioning** — Supports `major/minor/patch` three-level bumping, optional `.final` (approved) and `.refer` (reference) suffixes
- 📦 **Auto archiving** — Old versions are automatically moved to `history/` or `refer/` subdirectories when a document is modified, with zero residue
- ⚙️ **Config-driven** — Dual-source merging (skill config + workspace config), fully soft-fallback — never halts due to missing configuration
- 🔧 **CLI + Python API** — Pure standard library implementation, zero external dependencies, runs on Python 3.10+

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/document-naming.git
cd document-naming
```

### 30-Second Demo

```bash
# Generate a compliant filename
python scripts/naming.py generate "Content Strategy" md --type guide --author Hawk

# Bump version
python scripts/naming.py bump "guide_Content-Strategy_20260625_v1.0.0_Hawk.md" minor

# Archive old version
python scripts/naming.py archive "guide_Content-Strategy_20260625_v1.0.0_Hawk.md"
```

### Python Usage

```python
from naming import generate_name, bump_version, archive_old_version, parse_filename

# Generate a compliant filename (no disk I/O)
result = generate_name("Content Strategy", "md", file_type="guide", author="Hawk")

# Bump version
bumped = bump_version("guide_Content-Strategy_20260625_v1.0.0_Hawk.md", "minor")

# Archive old version
dest = archive_old_version("guide_Content-Strategy_20260625_v1.0.0_Hawk.md")

# Parse a compliant filename
parsed = parse_filename("guide_Content-Strategy_20260625_v1.0.0_Hawk.md")
```

## Naming Format

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

Example: `guide_content-strategy_20260407_v1.0.0_Hawk.md`

### Field Definitions

| Field | Rules |
|-------|-------|
| **Type** | Resolved by Step 1; can be any non-empty string. Linked to L1 directory via workspace config's "directory→type mapping" |
| **Title** | ≤ 30 characters; automatically removes `\/:*?"<>|` and whitespace. Error if empty after cleaning |
| **Date** | `YYYYMMDD`, always the current date |
| **Version** | `v<major>.<minor>.<patch>` — semantic versioning. New documents default to `v1.0.0` |
| **Suffix** | Optional `.final` (approved/finalized) or `.refer` (reference/backup) |
| **Author** | Priority: caller-provided → `config.json` → `"Unknown"` |
| **Extension** | Priority: caller-provided → `config.json` → `.md` |

### Version Policy

| Bump Level | When to Use |
|------------|-------------|
| `major` | Complete restructuring of topic, content, or framework |
| `minor` | Content additions, deletions, or rewrite |
| `patch` | Format fixes, grammar, typo corrections |

### Version Suffixes & Archive Routing

| Suffix | Meaning | Archive Behavior |
|--------|---------|------------------|
| (none) | Work in progress | Move to `history/` |
| `.final` | Approved/finalized | **Do not move** — stays in place |
| `.refer` | Reference/backup | Move to `refer/` |

## Workflow

All operations involving document creation or modification must invoke this skill first.

**Iron rule**: Never construct filenames manually, never skip the 3-step workflow, never distinguish between "major" and "minor" changes.

### Step 1 — Type Matching (`create`)

Resolves the filename prefix based on workspace config's "directory→type mapping":

| Scenario | Behavior |
|----------|----------|
| Caller provides a type that matches a known type | Normalize to the matched type |
| Caller provides a type that doesn't match any known type | Keep the caller's type (no error) |
| Caller doesn't provide a type | Use `fallback_dir_name` (default `"other"`) |

### Step 2 — File Generation (`create` + `modify`)

**Create**: Generates a compliant filename based on the type resolved in Step 1, determines the save path, and writes the file.

Save path rules:
- **L1**: Type matches a directory mapping → use the mapped directory; no match → `99 <fallback_dir_name>/`
- **L2**: Follow workspace config's sub-directory structure; create if not exists

**Modify**:
1. Parse the version segment from the existing compliant filename
2. Bump semantic version (`major/minor/patch`)
3. Refresh the date to current day
4. Replace only version and date — title, type, author, and extension remain unchanged
5. Write the new file to the original directory; the old file is archived by Step 3

### Step 3 — File Archive (`modify`)

After modification, automatically move the old version file to the corresponding subdirectory:

| Suffix | Target Directory | Config Key | Default |
|--------|------------------|------------|---------|
| (none) | `<source_dir>/history/` | `archive_dir_name` | `history` |
| `.refer` | `<source_dir>/refer/` | `refer_dir_name` | `refer` |
| `.final` | **Do not move** | — | — |

Archive flow: verify source file → route to target directory → create directory → **move** file → verify source file deleted

> **Critical**: Always use move operations (`mv`/`Move-Item`/`shutil.move`), never copy, to prevent old versions from remaining in the main directory.

| Platform | Correct | Wrong |
|----------|---------|-------|
| Git Bash | `mv` | ~~`cp`~~ |
| PowerShell | `Move-Item` | ~~`Copy-Item`~~ |
| Python | `shutil.move()` | ~~`shutil.copy()`~~ |

## Configuration

Runtime configuration is merged from two sources. Either source being unreadable will not halt execution:

| Source | File | Provides |
|--------|------|----------|
| **Skill config** | `config.json` | `default_author`, `default_extension`, `default_workspace_root`, `workspace_config_path` |
| **Workspace config** | (path from `workspace_config_path`) | `workspace_root`, `archive_dir_name`, `refer_dir_name`, `fallback_dir_name`; directory→type mapping |

Fallback chain (all soft — never halt):

| Config Key | Priority |
|------------|----------|
| `workspace_root` | caller-specified → Desktop → context/system-matched directory |
| `archive_dir_name` | workspace config → `"history"` |
| `refer_dir_name` | workspace config → `"refer"` |
| `fallback_dir_name` | workspace config → `"other"` |
| `default_author` | `config.json` → `"Unknown"` |
| `default_extension` | `config.json` → `.md` |

### config.json Example

```json
{
  "default_author": "Hawk",
  "default_extension": "md",
  "default_workspace_root": "C:/Users/admin/Desktop/ContentCreationExpert",
  "workspace_config_path": "C:/Users/admin/.workbuddy/WORKSPACE.md"
}
```

## CLI Reference

```bash
# Generate a new filename
python scripts/naming.py generate <title> <ext> \
    --type <type> --author <author> \
    [--date YYYYMMDD] [--suffix final|refer]

# Bump version
python scripts/naming.py bump <filename> <major|minor|patch>

# Archive old version
python scripts/naming.py archive <file_path>
```

### Output Examples

```bash
# Generate
$ python scripts/naming.py generate "Content Strategy" md --type guide --author Hawk
{"name":"guide_Content-Strategy_20260625_v1.0.0_Hawk.md","type":"guide","title":"Content Strategy","date":"20260625","version":"v1.0.0","suffix":"","author":"Hawk","ext":"md"}

# Bump
$ python scripts/naming.py bump "guide_Content-Strategy_20260625_v1.0.0_Hawk.md" minor
{"old_name":"guide_Content-Strategy_20260625_v1.0.0_Hawk.md","new_name":"guide_Content-Strategy_20260625_v1.1.0_Hawk.md","old_version":"v1.0.0","new_version":"v1.1.0"}

# Archive
$ python scripts/naming.py archive "guide_Content-Strategy_20260625_v1.0.0_Hawk.md"
{"archived":".../guide_Content-Strategy_20260625_v1.0.0_Hawk.md","to":".../history/guide_Content-Strategy_20260625_v1.0.0_Hawk.md"}
```

## Python API Reference

| Function | Purpose |
|----------|---------|
| `generate_name(title, ext, file_type, author, date_str, suffix)` | Generate a compliant filename (no disk I/O), returns a structured dict |
| `bump_version(filename, level)` | Bump version + refresh date, returns old and new filename & version |
| `archive_old_version(file_path)` | Move old version to archive directory, returns target Path |
| `parse_filename(filename)` | Parse a compliant filename into a structured dict; returns None if non-compliant |

## Directory Structure

```
document-naming/
├── SKILL.md              # Skill control file (triggers, workflow, config docs)
├── config.json           # Skill-level default configuration
├── README.md             # Chinese documentation
├── README.en.md          # English documentation
├── references/
│   ├── rules.md          # Naming format spec, field definitions, version policy
│   ├── step1-type-matching.md   # Step 1 type matching rules
│   ├── step2-file-generation.md # Step 2 file generation rules
│   └── step3-file-archive.md    # Step 3 file archive rules
└── scripts/
    └── naming.py         # Naming tool (CLI + Python API)
```

## Requirements

- Python 3.10+ (uses `dict | None` type syntax)
- No external dependencies — pure standard library implementation

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## License

[MIT License](LICENSE)
