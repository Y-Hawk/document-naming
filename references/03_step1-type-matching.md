# Step 1 — Type Matching

**Applies to: `create`.**

Resolves the type prefix for the filename. Data source: `directory_tree` — each entry's `type` field only (no keyword mapping).

---

## Prerequisite

**Merged config** = the flattened dict returned by `naming.py` `_load_config()`. After flattening, all workspace keys (`workspace_root`, `directory_tree`, etc.) are top-level — never accessed via `config["workspace"]`.

**Mandatory validation (hard gate)**: Before Step 1, validate the requested file extension against `allowed_extensions` from merged config. If extension not in the whitelist → refuse execution immediately, no further steps.

Read merged config for `directory_tree`. If `enable_workspace_path` is `true` and `workspace_config_path` points to a readable file, that file's data takes priority over config dict values. If unavailable, fall back to config dict defaults.

---

## Type Resolution

| Scenario | Action |
|----------|--------|
| Caller type matches a known type prefix | Normalize to matched prefix |
| Caller type matches no known prefix | Keep caller type (no error) |
| Caller provides no type | Use `fallback_dir_name` (default `"other"`) |
