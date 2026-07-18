# Naming Rules

Canonical format specification for the document-naming skill.

**Merged config** = values parsed by `naming.py` from the SKILL.md `## Configuration` table (the single source). The `directory_tree` is read separately from `references/workspace.md`.

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
| **Type** | Any non-empty string. Resolved via Type Matching; mapped to L1 directory when available. When no type is provided, the skill auto-detects it from content and confirms with the user (timeout → auto-execute); if unclassifiable, falls back to `Other`. |
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

---

## Workspace Settings

The following are fixed conventions. They are **no longer** SKILL.md
`### Configuration` keys — `naming.py` enforces them directly, and their
authoritative values live in `references/workspace.md`:

- **Directory tree source** — always `references/workspace.md`. `naming.py` reads
  and writes that file (the `workspace_doc` config key was removed).
- **Default workspace root** — when `references/workspace.md` `## Workspace Root`
  is empty, `naming.py` creates and uses `<system user root>/DocumentSpace`
  (`system user root` = `Path.home()`, per OS). Never the bare Desktop / user-root.
  (The `default_workspace_root` config key was removed; this default is fixed.)
- **Archive / refer directory names** — defined in `references/workspace.md`
  `## Workspace Config` (`archive_dir_name` / `refer_dir_name`). Edit there to
  change them; the SKILL.md `### Configuration` table no longer carries them.
- **Explicit workspace root override** — there is no SKILL.md config key for the
  root; set it in `references/workspace.md` `## Workspace Root` instead.
