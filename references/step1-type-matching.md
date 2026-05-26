# Step 1 — Type Matching

**Applies to: `create` and `organize`.**

---

## Prerequisite

Read the workspace config document at the path specified in `config.json` → `workspace_config_path`.

If the config document cannot be read or the path is not configured, stop and report:

> `ERROR: workspace config document not found. Please configure "workspace_config_path" in config.json and ensure the file exists.`

---

## Type Resolution

Determine the type prefix to use in the filename.

| Scenario | Action |
|----------|--------|
| Caller provides a type, fuzzy-matches a standard type | Normalize to the standard type |
| Caller provides a type, unlike any standard type | Keep caller type as-is |
| Caller provides no type | Use `fallback_directory` from config.json; if not configured, default to `"other"` |

*Fuzzy-match examples: `guide` ~ `Plan`, `post` ~ `Article`, `report` ~ `Report` → normalize. `music`, `xyz123` → keep as-is.*

---

## Directory Resolution

Once the type is resolved, determine where the file is saved.

### Level 1 — First-Level Directory

- **Type matched a standard type** → use the mapped L1 directory from the workspace config document.
- **Type has no match** → use `99 <type>/` under the workspace root. Create if it does not exist.

### Level 2 — Sub-Directory

Determined by the workspace config document's sub-directory structure for the matched type.

If no sub-directory rule matches:
1. Auto-generate a meaningful L2 directory name from the document's topic or content.
2. Create the directory under the matched L1 directory.
3. Append the new sub-directory entry to the workspace config document.

---

## Mode-Specific Resolution

### Create

```
preferred: matched type → L1 directory + L2 sub-directory from workspace config
fallback:  file's L1 parent directory matched against workspace config; L2 auto-create if unmatched
default:   no directory match → `99 <fallback_directory>/`, auto-create if missing
```

### Organize

```
preferred: file's current type matches current directory → keep in place, rename type prefix only
fallback:  file's current type ≠ current directory → query workspace config for correct directory; L2 auto-create if unmatched → move + rename
default:   no matching directory found → keep in place, continue silently
```
