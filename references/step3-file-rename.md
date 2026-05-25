# Step 3 — File Rename

**Applies to: `organize` only.**

Changes the type prefix of a compliant file using the type from Step 1, and moves the file to the correct directory if the current directory does not match.

---

## Process

### 1. Verify Type-Directory Match

Before renaming, check whether the file's current first-level directory matches the type resolved in Step 1.

* **If type matches directory** → rename type prefix in place.
* **If type does NOT match directory** → query `references/workspace.md` for the directory that maps to the resolved type.
  * **If a matching directory is found** → move the file to that directory, then rename type prefix.
  * **If NO matching directory is found** → stop and report:
    > `ERROR: no directory found in workspace config for type "<type>". Cannot organize file.`

### 2. Rename

Type prefix is replaced. Title, date, version, author, extension are **never** changed when organizing.

**Example — same directory:**

```
old: 文章_AI-guide_20260523_v1.0.0_Kai.md   (in 04 文章/)
new: 指南_AI-guide_20260523_v1.0.0_Kai.md   (stays in 04 文章/, type prefix changed)
     ^^^^ type changed, everything else preserved
```

**Example — cross-directory move:**

```
old: 其它_AI-guide_20260523_v1.0.0_Kai.md   (in 99 其它/)
new: 指南_AI-guide_20260523_v1.0.0_Kai.md   (moved to 04 文章/, type prefix changed)
     ^^^^ type changed, file moved to correct directory
```

### 3. Execute

```bash
# Same directory — just rename
mv "文章_AI-guide_20260523_v1.0.0_Kai.md" "指南_AI-guide_20260523_v1.0.0_Kai.md"

# Cross-directory — move then rename
mv "99 其它/其它_AI-guide_20260523_v1.0.0_Kai.md" \
   "04 文章/指南_AI-guide_20260523_v1.0.0_Kai.md"
```

### Edge Cases

* **If new type equals existing type** → no change needed.
* **If target filename already exists in destination** → skip (no overwrite), report.
* **If file is outside workspace root** → stop, report error: cannot organize files outside workspace.
