# Naming Rules

Canonical format specification for the document-naming skill.

**Merged config** = values parsed by `naming.py` by merging `config.json` (baseline, may be remote-managed) with `config.local.json` (per-machine, git-ignored, key-level override). The `directory_tree` and `workspace_root` also live in these JSON files (`config.local.json` receives all runtime writes).

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
| (none) | Work in progress | Move to the language-matched archive folder — `history/` for an English filename, the Chinese folder for a Chinese filename |
| `.final` | Approved / finalized | **Stay in place** |
| `.refer` | Reference / backup | Move to the language-matched refer folder — `refer/` for an English filename, the Chinese folder for a Chinese filename |

> Archive / refer folder names are **not configurable** — they are fixed rules matched to the document's language. A filename containing any CJK character (`[\u4e00-\u9fff]`) counts as Chinese; otherwise English.

---

## Workspace Settings

Workspace-related settings live in the JSON config files (`config.json` +
`config.local.json`), not in SKILL.md and not in `references/workspace.md`:

- **Directory tree source** — the `directory_tree` key in the merged config.
  `naming.py` reads it from the merge and writes updates only to
  `config.local.json` (the per-machine, git-ignored file). `references/workspace.md`
  is documentation only; it no longer stores the tree.
- **Workspace root** — the `workspace_root` key in the merged config
  (`config.local.json` overrides `config.json`). When it is empty, `naming.py`
  creates and uses `<system user root>/DocumentSpace` (`system user root` =
  `Path.home()`, per OS). Never the bare Desktop / user-root.
- **Archive / refer directory names** — **not configurable**. They are fixed
  language-matched rules (see Version Policy → Suffix): a Chinese filename →
  the Chinese archive folder (none) / the Chinese refer folder (`.refer`); an
  English filename → `history/` / `refer/`.
- **Per-machine isolation** — all runtime writes (scan / upsert / root) land in
  `config.local.json`, so remote-managed `config.json` never gets clobbered and
  different machines keep their own root and tree.
