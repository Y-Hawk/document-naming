# Step 1 — Type Matching

**Applies to: `create` and `organize`.**

Resolve the correct type prefix for the filename using the workspace config document.

---

## Process

1. Read the workspace config document at the path specified in `config.json` → `workspace_config_path`.
   * **If the config document cannot be read or the path is not configured**, stop immediately and report:
     > `ERROR: workspace config document not found. Please configure "workspace_config_path" in config.json and ensure the file exists.`

2. Look up the target directory in the Directory→Type Mapping table to get the type prefix.
   * **If the directory is not found in the mapping**, stop immediately and report:
     > `ERROR: directory "<dir>" is not listed in the workspace config. Please add it to references/workspace.md or place the file under a known first-level directory.`

3. Use the resolved type for subsequent steps.

---

## Save Path Resolution

### Create

```
save path resolution (create):
  preferred: workspace config → target directory for the resolved type
  error: if workspace config is unavailable or type not in mapping → stop, report error
```

### Organize

```
save path resolution (organize):
  preferred: file's current type matches current directory type → keep file in place, only rename type prefix
  error:    file's current type does NOT match current directory → query workspace config to find correct directory → move file there, then rename type prefix
  error:    no matching directory found in workspace config for the file's type → stop, report error
```

---

## Type Resolution Chain

```
type resolution:
  preferred: workspace config document → directory-mapped type
  fallback:  file's first-level parent directory matched against workspace config
  error:     no match found → stop, report error (do not silently apply a default)
```
