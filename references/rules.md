# Workspace Management Rules

## Standard Format

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

Example: `guide_claw-content-strategy_20260407_v1.0.0_Kai.md`

---

## Fields

| Field | Rule |
|-------|------|
| Type | Resolved through Step 1 chain: workspace config → directory-name match. **If no match found: keep original/caller-provided type, do NOT report error.** |
| Title | ≤ 30 chars. `\/:*?"<>|` stripped. Spaces collapsed. **Error if empty after sanitisation.** |
| Date | `YYYYMMDD`. Today by default. Refreshed on modify. Preserved on organize |
| Version | `v1.0.0` for new documents. Append `.final` (final/approved) or `.refer` (reference/backup) if caller specifies |
| Author | Caller context (SOUL.md / IDENTITY.md) → config.json `default_author`. **Error if not configured.** |
| Extension | Caller-provided → config.json `default_extension`. **Silent default `.md` when not configured.** |

---

## Version Policy

### Segment Bumping

| Level | When |
|-------|------|
| `major` | Full restructure of topic / content / framework |
| `minor` | Content revisions — additions, deletions, changes |
| `patch` | Format fixes, grammar, typo corrections |

### Suffix

| Suffix | When |
|--------|------|
| (none) | Default — work in progress |
| `.final` | Caller confirms version is final / approved / done |
| `.refer` | Caller marks version as reference / backup / archival |

### Mode-Specific Behaviour

- **Create**: default `v1.0.0`. If caller specifies final or reference intent, append `.final` or `.refer`.
- **Modify**: bump first 3 segments per Segment Bumping rules, then append `.final` / `.refer` if caller specifies. Refresh date to today. Create new file, write modified content.
- **Organize**: version and date preserved (no bump, no refresh), including suffix.

---

## Workspace Config Integration

This skill reads the workspace config document (path: `config.json` → `workspace_config_path`) for directory→type mapping in Step 1.

### Error Handling

- **Workspace config unavailable or path not configured** → stop, report `ERROR: workspace config document not found. Please configure "workspace_config_path" in config.json.`
- **Directory not in mapping** → keep original/caller-provided type, continue silently (do NOT report error).
- **Type mismatch with directory (organize)** → auto-change type prefix to match the directory, rename file, continue silently (do NOT report error).
