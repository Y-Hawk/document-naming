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
| **Type** | Any non-empty string. Resolved via **3-tier Type Resolution** (below): (1) config match — title/content matched against existing L1 `type` values; (2) AI defines a new type from content; (3) default type adapted to the document language (`其它` for Chinese, `Other` for English), reusing the `99 其它` entry. The resolved type is mapped to the L1 directory when available. When no type is supplied and the AI cannot classify, it falls back to the language-adapted default type. |
| **Title** | ≤ 30 chars. Strip `\/:*?"<>|` and whitespace. Empty after sanitisation → fallback `"untitled"`. |
| **Date** | `YYYYMMDD`, always today. |
| **Version** | `v<major>.<minor>.<patch>`. New documents start at `v1.0.0`. Optional `.final` / `.refer` suffix. |
| **Author** | Merged config `default_author` → caller-provided `--author` → `"Unknown"`. |
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
`config.local.json`), not in `references/workspace.md`:

- **Directory tree source** — the `directory_tree` key in the merged config.
  `naming.py` reads it from the merge and writes updates only to
  `config.local.json` (the per-machine, git-ignored file). `references/workspace.md`
  is documentation only; it no longer stores the tree. The merged config is
  authoritative; the tree is **additively synced from disk** each call (see below).
- **Workspace root** — the `workspace_root` key in the merged config
  (`config.local.json` overrides `config.json`). Resolution is **4-tier**
  (see below). The static config always wins over an explicit/context root for
  the **root itself**; "user highest priority" applies only to the L1/L2
  save-directory choice.
- **Archive / refer directory names** — **not configurable**. They are fixed
  language-matched rules (see Version Policy → Suffix): a Chinese filename →
  the Chinese archive folder (none) / the Chinese refer folder (`.refer`); an
  English filename → `history/` / `refer/`.
- **Per-invocation additive sync (no delete)** — on every call, if a root is
  **configured** (`source` ∈ {`config`, `root`, `context`}), the config tree is
  additively synced from disk: any numbered content L1/L2 directory present on
  disk but missing from the config tree is added (its number preserved). Config
  entries absent on disk are **never** removed — the config tree is the category
  source of truth, so deletions are not auto-pruned. When the root is the
  fallback (`source=default`), no sync runs. `naming.py scan --apply` is the
  explicit full mirror for a one-off forced reconciliation.
- **Per-machine isolation** — all runtime writes (upsert / root / additive sync)
  land in `config.local.json`, so remote-managed `config.json` never gets
  clobbered and different machines keep their own root and tree.

---

## Workspace Root Resolution (4-tier, config-first)

The root directory MUST be determined before any save-path decision. Resolution
is **config-first**, four tiers:

1. **Configured root** — `workspace_root` in the merged config (config.local.json
   overrides config.json) is non-empty → use it (authoritative, highest).
   `source=config`.
2. **Explicit root provided** — config empty + `--root` / `--workspace-root` passed
   (user/AI explicit) → adopt it **and persist** into `config.local.json` (becomes
   the future config). `source=root`.
3. **Context-inferred root** — config empty + no explicit root + `--context-root` /
   `--context-workspace-root` passed (AI inferred from session) → use it, **never
   persisted** (re-inferred each run). `source=context`.
4. **Fallback** — config empty + nothing provided → `<system user root>/DocumentSpace`
   (auto-created, where `<system user root>` = `Path.home()`). `source=default`.

> A user-specified root is **lower priority than an existing config root** — it
> only takes effect (and persists) when the config root is empty. "User highest
> priority" applies to the **L1/L2 save-directory** choice, not to overriding an
> already-configured root.

---

## Type Resolution (3-tier, content-driven)

The document type (filename prefix and L1 category) is resolved for **every**
document through three tiers, in order:

1. **Config match (highest for type)** — read the `directory_tree` and match the
   document's title (then, if needed, its first ~200 chars of body content)
   against the existing L1 `type` values. If a config type matches → use it
   (mapped to that L1 directory).
2. **AI defines a new type** — if no config type matches (or the config tree is
   unreadable) → the AI autonomously defines a new type from the content, then
   creates it via `upsert` (persisted to config). L1 numbering is auto-assigned.
3. **Default type (fallback)** — if the AI also cannot define a type → use the
   skill's default type, **adapted to the document language**: Chinese → `其它`,
   English → `Other`. The default category is the `99 其它` entry in config; the
   filename prefix adapts to the language while the directory stays `99 其它`.

Notes:
- The detected language governs the **title and content wording**, not the
  directory structure or the type prefix. Do not create parallel English-named
  L1 directories — reuse the existing L1 that matches the concept.
- If a genuinely new concept appears, create it under the tree via `upsert`.
- Auto-detection (tiers 1–2 when no type is supplied) requires user confirmation
  before a *new* directory is created; timeout → auto-execute (SKILL.md
  Constraint #8).

---

## Save Directory Resolution (4-step, premised on a determined root)

Once the root is determined (above), resolve the **save directory** through four
steps:

1. **User explicitly specifies L1/L2** → highest priority; save there. Overrides
   config-tree matching.
2. **User unspecified** → read the `directory_tree` and match by type:
   - L1 hit + L2 hit → save under that L2.
   - L1 hit + no suitable L2 → create the L2 from AI context under that L1, save
     there.
   - No L1 hit → create the L1 for the type, and create the L2 from AI context
     under it, save there.
3. Any newly created L1/L2 is **upserted into the config tree** (persisted) via
   `naming.py upsert`, and the directory is created on disk.
4. The resolved `save_path` is returned by `naming.py generate` (it auto-upserts
   and reports `save_path`, `l1`, `l2`).

> "User highest priority" lives here: an explicit user save location overrides
> config matching. It does NOT override an already-configured **root** (see
> Workspace Root Resolution step 1).

---

## Resolution Priority

Three values — `default_author`, `workspace_root`, and `directory_tree` — resolve
through a priority chain. The **merged config is authoritative**; an explicit
context flag fills the gap (and may persist); the context-inferred root fills the
next gap (never persisted); the hardcoded fallback is last.

| Value | 1. Config (authoritative) | 2. Explicit (persisted) | 3. Context-inferred (not persisted) | 4. Fallback |
|-------|---------------------------|-------------------------|--------------------------------------|-------------|
| `default_author` | merged `default_author` | `--author <name>` | — | `"Unknown"` |
| `workspace_root` | merged `workspace_root` | `--root` / `--workspace-root` (writes config.local.json) | `--context-root` / `--context-workspace-root` | `<user-home>/DocumentSpace` (created) |
| `directory_tree` | merged `directory_tree` (authoritative) | — | — | additively synced from disk each call (no delete) |

Notes:
- The explicit context for `default_author` / `workspace_root` is supplied by the
  calling AI as the `--author` / `--root` flags. It never overrides an explicit
  config value; `--root` only takes effect (and persists) when the config has no
  root.
- `--context-root` is the AI's session-inferred root; it is used only when the
  config has no root and no explicit root was provided, and it is **never**
  written to any config file.
- `directory_tree` has no explicit/context tier; the merged config is authoritative
  and is kept in lock-step with disk through the per-invocation **additive** sync
  (additions only — never prune). For a forced full mirror, use
  `naming.py scan --apply`.
- This ordering is why "config reading is fine": the static config stays the top
  layer, the explicit/context root is a middle gap-filler, and the hardcoded
  default is the final safety net.
