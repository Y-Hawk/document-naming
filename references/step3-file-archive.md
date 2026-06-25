# Step 3 — File Archive

**Applies to: `modify` only.**

After Step 2 creates the new versioned file, move the old file to the appropriate sub-directory based on its version suffix.

---

## Process

| Step | Action |
|------|--------|
| **1. Verify** | Source file exists. Missing → error: `source file "<path>" not found` |
| **2. Route** | See suffix routing table below |
| **3. Create** | Create target sub-directory if missing. Failure → error |
| **4. Move** | Move file into target directory. Name collision → append `_1`, `_2`, ... |
| **5. Verify** | Confirm source file NO LONGER EXISTS at original path. If still present → **delete it**. This is mandatory. |

> **CRITICAL — Move vs Copy**: Step 4 MUST use a **move** operation, NOT copy. Using `cp`/`Copy-Item` without deleting the source afterward will leave stale old versions in the main directory. See platform commands below.

### Suffix Routing

| Suffix | Target | Config Key | Default |
|--------|--------|-----------|---------|
| (none) | `<source_parent>/<archive_dir_name>/` | `archive_dir_name` | `"history"` |
| `.refer` | `<source_parent>/<refer_dir_name>/` | `refer_dir_name` | `"refer"` |
| `.final` | **Do NOT move** — file stays in place | — | — |

Config keys read from workspace config Configuration table. Not configured → use default.

---

## Platform Commands

| Platform | Correct (Move) | Wrong — DO NOT USE |
|----------|---------------|---------------------|
| Git Bash | `mv "source" "target/"` | ~~`cp "source" "target/"`~~ |
| PowerShell | `Move-Item "source" "target/"` | ~~`Copy-Item "source" "target/"`~~ |
| Python | `shutil.move(src, dst)` | ~~`shutil.copy(src, dst)`~~ |

> Use `mv`/`Move-Item`/`shutil.move` — these remove the source file **automatically**. If you must verify, check source path does not exist after the operation.

---

## CLI

```bash
python scripts/naming.py archive "<path>/guide_AI-guide_20260520_v1.0.0_Hawk.md"
```

```json
// output
{"archived": ".../guide_AI-guide_20260520_v1.0.0_Hawk.md", "to": ".../<target_dir>/guide_AI-guide_20260520_v1.0.0_Hawk.md"}
```
