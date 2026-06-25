# Naming Rules

Canonical format specification for the document-naming skill. All filename generation, parsing, and validation follow these rules.

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
| Type | Resolved via Step 1. Can be any non-empty string — no enum, no validation. Mapped to L1 directory via workspace config Directory→Type Mapping when available. |
| Title | ≤ 30 chars, `\/:*?"<>|` stripped, whitespace removed. **Error if empty after sanitisation.** |
| Date | `YYYYMMDD`. Always today — new documents and modified versions both use the current date. |
| Version | `v<major>.<minor>.<patch>` — semantic versioning. `v1.0.0` for new documents. Optional `.final` (approved) or `.refer` (reference) suffix after version. |
| Author | SOUL.md / IDENTITY.md → `config.json` `default_author` → `"Unknown"`. |
| Extension | Caller-provided → `config.json` `default_extension` → `.md` (silent). |

---

## Version Policy

### Segment Bumping

| Level | When |
|-------|------|
| `major` | Full restructure of topic / content / framework |
| `minor` | Content changes — additions, deletions, rewrites |
| `patch` | Format fixes, grammar, typo corrections |

### Suffix

| Suffix | When | Behaviour |
|--------|------|-----------|
| (none) | Default — work in progress | Archives to `<archive_dir_name>/` (Step 3) |
| `.final` | Caller confirms version is final / approved / done | **Not moved** (Step 3) |
| `.refer` | Caller marks version as reference / backup | Archives to `<refer_dir_name>/` (Step 3) |

---

## Usage by Operation

| Operation | Step | What happens |
|-----------|------|-------------|
| **Create** | Step 1 → 2 | Resolve type, generate filename `v1.0.0`, write to L1/L2 directory |
| **Modify** | Step 2 → 3 | Bump version + date = today → write new file → archive old file based on suffix |

Full workflow details: [SKILL.md](../SKILL.md) → 3-Step Workflow table.
