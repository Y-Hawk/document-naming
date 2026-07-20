# File Archive
**Applies to: `modify` only** — i.e. the target `save_path` already contains a file of the same document with a *different* version.

**MUST run BEFORE the new version is written.** The object of this step is the
**original old file** that already exists on disk — move it into the archive
folder first, then (or as part of) generating/writing the new version. Never let
the new content overwrite the original in place.

**Merged config** = the dict returned by `naming.py` `_load_config()` (merge of
`config.json` + `config.local.json`). Archive / refer folder names are **not**
config keys — they are fixed rules matched to the **old (source) file's**
language (any CJK char in the old filename → Chinese folder, else English).

`naming.py generate` performs this automatically: it detects the existing old
version in the target directory and moves it **before** returning, populating
`archive_path`. You normally do not archive by hand — but if you do, follow the
Process below.

---

## Process

| Step | Action |
|------|--------|
| **1. Verify** | Source file exists. Missing → error |
| **2. Route** | See suffix routing table below |
| **3. Create** | Target sub-directory if missing |
| **4. Move** | Move file to target. Name collision → append `_1`, `_2`, ... |
| **5. Verify** | Source file no longer exists at original path. If still present → delete it |

### Suffix Routing

Target folder name is matched to the **document's language**, decided by the
source filename: any CJK character (`[\u4e00-\u9fff]`) → Chinese, else English.

| Suffix | Chinese filename | English filename |
|--------|------------------|------------------|
| (none) | `<source_parent>/<Chinese archive folder>/` | `<source_parent>/history/` |
| `.refer` | `<source_parent>/<Chinese refer folder>/` | `<source_parent>/refer/` |
| `.final` | **Not moved** — stays in place | **Not moved** — stays in place |

> Suffix routing defined in [rules.md](rules.md) Version Policy → Suffix table.

---

## Move vs Copy

**CRITICAL**: Use **move** operations only. Never copy — copies leave stale old versions in the main directory.

| Platform | Correct |
|----------|---------|
| Git Bash | `mv "source" "target/"` |
| PowerShell | `Move-Item "source" "target/"` |
| Python | `shutil.move(src, dst)` |
