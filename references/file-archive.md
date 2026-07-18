# File Archive
**Applies to: `modify` only.**

**Merged config** = the dict returned by `naming.py` `_load_config()`. Settings such as `archive_dir_name` / `refer_dir_name` are top-level — never accessed via a nested `config["workspace"]` key.

After File Generation creates the new versioned file, move the old file to a sub-directory based on its suffix.

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

| Suffix | Target | Default |
|--------|--------|---------|
| (none) | `<source_parent>/<archive_dir_name>/` | `history` |
| `.refer` | `<source_parent>/<refer_dir_name>/` | `refer` |
| `.final` | **Not moved** — stays in place | — |

> Suffix routing defined in [rules.md](rules.md) Version Policy → Suffix table.

---

## Move vs Copy

**CRITICAL**: Use **move** operations only. Never copy — copies leave stale old versions in the main directory.

| Platform | Correct |
|----------|---------|
| Git Bash | `mv "source" "target/"` |
| PowerShell | `Move-Item "source" "target/"` |
| Python | `shutil.move(src, dst)` |
