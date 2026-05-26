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
