# Step 1 — Type Matching

**Applies to: `create`.**

Resolves the type prefix to use in the filename. Reads workspace config for directory→type mapping.

---

## Prerequisite

Read `config.json` → `workspace_config_path` for the workspace config document. If unavailable, warn and continue — skill remains operational with `config.json` defaults. See [SKILL.md](../SKILL.md) → Configuration for fallback rules.

---

## Type Resolution

| Scenario | Action |
|----------|--------|
| Caller provides a type, and it matches a known type from workspace config | Normalize to the matched type |
| Caller provides a type, but it does not match any known type | Keep caller type as-is (do NOT error) |
| Caller provides no type | Use `fallback_dir_name` from workspace config (default `"other"`) |

The resolved type is passed to Step 2 for L1 directory mapping and filename generation.
