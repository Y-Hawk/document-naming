# Workspace Management Rules

## Standard Format

```
Type_Title_YYYYMMDD_v1.0.0_Author.ext
```

Example: `guide_claw-content-strategy_20260407_v1.0.0_Kai.md`

---

## Fields

| Field | Rule |
|-------|------|
| Type | Resolved through Step 1 chain: workspace config → directory-name match. **If no match found: keep original/caller-provided type, do NOT report error.** |
| Title | ≤ 30 chars. `\/:*?"<>|` stripped. Spaces collapsed. **Error if empty after sanitisation.** |
| Date | `YYYYMMDD`. Today by default. Refreshed on modify. Preserved on organize |
| Version | Always `v1.0.0` for new documents |
| Author | Caller context (SOUL.md / IDENTITY.md) → config.json `default_author`. **Error if not configured.** |
| Extension | Caller-provided → config.json `default_extension`. **Silent default `.md` when not configured.** |

---

## Version Policy

| Level | When |
|-------|------|
| `major` | Full restructure of topic / content / framework |
| `minor` | Content revisions — additions, deletions, changes |
| `patch` | Format fixes, grammar, typo corrections |

- **New documents**: always `v1.0.0`
- **Modify**: bump version + refresh date to today, create new file, write modified content
- **Organize**: version and date preserved (no bump, no refresh)

---

## Workspace Config Integration

This skill reads the workspace config document (path: `config.json` → `workspace_config_path`) for directory→type mapping in Step 1.

### Error Handling

- **Workspace config unavailable or path not configured** → stop, report `ERROR: workspace config document not found. Please configure "workspace_config_path" in config.json.`
- **Directory not in mapping** → keep original/caller-provided type, continue silently (do NOT report error).
- **Type has no matching directory (organize)** → keep file in place, rename type prefix only, continue silently (do NOT report error).
