# Naming Rules

Canonical format specification for the document-naming skill.

**Merged config** = the flattened dict returned by `naming.py` `_load_config()`. After flattening, all workspace keys (`workspace_root`, `directory_tree`, etc.) are top-level — never accessed via `config["workspace"]`.

---

## Standard Format

```
Type_Title_YYYYMMDD_v<major.minor.patch>[.final|.refer]_Author.ext
```

Example: `guide_claw-content-strategy_20260407_v1.0.0_Hawk.md`

---

## Fields

| Field | Rules |
|-------|-------|
| **Type** | Any non-empty string. Resolved via Step 1; mapped to L1 directory when available. When no type provided, `fallback_dir_name` used as type prefix — must be pure ASCII, no numeric prefix or spaces. |
| **Title** | ≤ 30 chars. Strip `\/:*?"<>|` and whitespace. Empty after sanitisation → fallback `"untitled"`. |
| **Date** | `YYYYMMDD`, always today. |
| **Version** | `v<major>.<minor>.<patch>`. New documents start at `v1.0.0`. Optional `.final` / `.refer` suffix. |
| **Author** | Caller-provided → merged config `default_author` → `"Unknown"`. |
| **Extension** | Caller-provided → merged config `default_extension` → `md` (no leading dot). **Mandatory validation**: must be in `allowed_extensions` whitelist; if not, refuse execution. |

---

## Version Policy

### Segment Bumping

| Level | When |
|-------|------|
| `major` | Full restructure of topic / content / framework |
| `minor` | Content additions, deletions, or rewrites |
| `patch` | Format fixes, grammar, typo corrections |

### Suffix

| Suffix | Meaning | Archive behaviour |
|--------|---------|-------------------|
| (none) | Work in progress | Move to `<archive_dir_name>/` |
| `.final` | Approved / finalized | **Stay in place** |
| `.refer` | Reference / backup | Move to `<refer_dir_name>/` |
