# Step 4 — File Archive

**Applies to: `modify` only.**

After Step 2 creates the new versioned file, move the old file to the archive sub-directory.

---

## Process

1. **Verify source file exists.** Error if missing:
   > `ERROR: source file "<path>" not found. Cannot archive.`

2. **Create archive sub-directory** if it does not exist:
   * Directory name from `config.json` → `archive_dir_name`.
   * **If `archive_dir_name` is not configured** → stop, report error:
     > `ERROR: missing config key "archive_dir_name" in config.json. Please configure it.`
   * Directory path: `<parent>/<archive_dir_name>/`

3. **Move file** into archive sub-directory.

4. **Handle name collisions** inside the archive directory: if the target filename already exists, append `_1`, `_2`, ... numeric suffix (before extension).

---

## Run the Script

```bash
python scripts/naming.py archive \
    "<dir>/指南_AI-guide_20260520_v1.0.0_Kai.md"
```

## Output

```json
{
  "archived": ".../指南_AI-guide_20260520_v1.0.0_Kai.md",
  "to": ".../history/指南_AI-guide_20260520_v1.0.0_Kai.md"
}
```

---

## Edge Cases

| Case | Handling |
|------|----------|
| Source file missing | Stop, report error |
| `archive_dir_name` not in config | Stop, report error |
| Archive collision | Append `_1`, `_2`, ... numeric suffix |
| Archive directory creation fails | Stop, report filesystem error |
