# Quality Self-Checklist

Run after filename generation and before archiving. P0 must pass before output.

> This file is the QA checklist for document-naming — the final QA gate run before delivering any filename.

---

## QA Principles

1. **Check before output**: complete all checks before returning results
2. **P0 zero-tolerance**: P0 failures must be fixed and re-verified
3. **P1 must fix**: P1 issues should be fixed before output
4. **P2 advisory**: P2 issues recorded but do not block

---

## Checklist

### 1. Extension Validation

- [ ] File extension is in `allowed_extensions` whitelist
  - **P0**: extension not in whitelist → refuse execution immediately
  - **P1**: extension has leading dot → strip and re-check

### 2. Type Matching

- [ ] Document language detected from title/content before type matching
  - **P1**: language not detected or defaulted to English → re-detect from content
  - **P2**: mixed-language document → use primary language (majority of content)
- [ ] Type resolved against `directory_tree` for every document; detected language governs title/content only
  - **P1**: type not matched to the tree → auto-detect from content and confirm with user (timeout → auto-execute)
  - **P1**: document about to create a parallel/new L1 for an existing concept → reuse the matching L1 already defined in the `directory_tree` instead
  - **P2**: mixed-language document → use primary language (majority of content) for the title
- [ ] Type prefix resolved from `directory_tree` or kept as-is
  - **P1**: type matches no known prefix → auto-detect from content and confirm with user (timeout → auto-execute)
  - **P2**: type could match multiple entries → document ambiguity
- [ ] No type supplied → skill MUST propose a type and **confirm with the user (timeout → auto-execute) before creating any new directory**
  - **P1**: a new L1/L2 directory was created without first proposing + confirming the type (or without the timeout fallback) → reject; run `naming.py upsert` only after confirmation
  - **P2**: confirmation prompt omitted the "auto-creates directory + syncs config.local.json" notice → re-prompt with full notice

### 3. Filename Format

- [ ] Filename follows `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}` format
  - **P0**: missing required fields (type/date/author) → reject
  - **P1**: version format incorrect → correct to semver
  - **P2**: title contains special characters → suggest sanitization

### 4. Version Management

- [ ] Version bump (major/minor/patch) correctly applied
  - **P1**: bump type doesn't match change → suggest correct level
  - **P2**: version string format edge case → normalize
- [ ] **Deterministic bump chain (constraint #12 gate)**: on `modify`, the AI MUST compute the next version by calling `naming.py bump <existing_full_filename> <major|minor|patch>`, then pass that exact version to `naming.py generate --version <x.y.z>`. Never hand-edit or guess the version.
  - **P0**: a `modify` whose new version was hand-written / guessed (not derived from `bump`) → reject; recompute via `bump` then chain `generate --version`
  - **P0**: `generate` returned no `archive_path` on a `modify` (old same-doc file still in the original directory) → this is an in-place overwrite; refuse delivery, run archive first
  - **P1**: `generate` was called without `--version` on a `modify` → the version is unchained from `bump`; re-run the `bump → generate --version` chain
  - **P2**: `bump` scope (major/minor/patch) mismatched the actual change → suggest the correct scope
- [ ] **No orphan `bump` + in-place edit (P0 gate)**: on `modify`, the AI MUST complete the full `bump → generate --version → Write new content to returned save_path` chain. `bump` alone computes only a version string — it performs NO disk I/O (no archive, no write). The archive step lives inside `generate`, so **skipping `generate` and instead `Edit`-ing the existing file in place leaves the filename at the OLD version while content changes silently** — this is a silent in-place overwrite masquerading as a version bump.
  - **P0**: a `modify` where `bump` was run but `generate --version` was never called, and the new content was written via in-place `Edit`/`Write` to the OLD filename → reject; run the full chain, then `Write` the new content to the `save_path`/`name` that `generate` returned (a different filename than the old one)
  - **P0**: after delivery, the old-version filename still exists in the original directory AND no `archive_path` was returned → the file was never archived; refuse, run `generate` (which auto-archives) before writing

### 5. Archive

- [ ] **Modify detection + mandatory archive (P0 gate)**: if the target `save_path` already contains a file of the same document (same type/title/author/ext, a *different* version), this is a modify and the old version MUST be archived (moved) **before** the new file is written. `generate` returns `archive_path` on modify — verify it is present and the old file is no longer at its original path.
  - **P0**: a modify where the old file was NOT moved and `archive_path` is absent (or the old file still sits in the original directory alongside the new one) → this is an **in-place overwrite**; refuse delivery, run archive first
  - **P0**: archive via move, not copy (data loss risk if copy+delete)
  - **P1**: archive directory doesn't exist → create it
  - **P1**: folder language does not match the **old** file's language (e.g. Chinese old file archived to `history/`) → re-route to the correct language folder
  - **P2**: multiple old versions could be consolidated

### 6. Path & Cross-Reference

- [ ] Workspace root resolved via the 4-tier chain (SKILL.md constraint #9): configured root > explicit `--root` (persisted when config empty) > `--context-root` (session-inferred, never persisted) > `DocumentSpace` fallback; a static config root always wins over explicit/context roots
  - **P1**: an explicit/context root overrode a non-empty configured root → keep the configured root; explicit/context roots apply only when config is empty
  - **P2**: `--context-root` got persisted into config.local.json → it must never be persisted (re-inferred each run); only `--root` persists
- [ ] Config loaded by merging `config.json` (baseline) + `config.local.json` (per-machine override); tree + workspace_root come from the same merge
  - **P0**: both `config.json` and `config.local.json` missing/unparseable → error with guidance (soft-fail to `{}` per file is tolerated)
  - **P1**: `directory_tree` value in the merged config unparseable → fix or rebuild it in `config.local.json`
  - **P2**: directory created but not synced to `config.local.json` → run `naming.py upsert` to sync
- [ ] **Baseline `config.json` is never written by the script (constraint #3)**: all runtime tree/root writes land in `config.local.json` only; `config.json` stays the immutable baseline (local override wins on merge)
  - **P2**: a runtime write targeted `config.json` (or it changed during a session) → revert the change and route the write to `config.local.json` (key-level override)
- [ ] User-specified save location takes highest priority (SKILL.md constraint #10): an explicit user L1/L2 (or full path) overrides config-tree matching, but does NOT override an already-configured root (root follows its own 4-tier chain)
  - **P1**: user explicitly named an L1/L2/path but config-tree matching silently redirected the file elsewhere → honor the user location, then `upsert` it into the tree
  - **P2**: user-specified location was treated as a new root instead of a save directory → keep the configured root; apply the user choice only to the save directory
- [ ] Per-invocation sync is additive only (SKILL.md constraint #11): when a root is configured (`source ≠ default`), new on-disk L1/L2 dirs are added to the config tree; config entries missing on disk are NEVER auto-removed
  - **P1**: a config-tree entry was pruned/deleted because it no longer exists on disk → restore it; deletions are never auto-pruned (only `scan --apply` performs an explicit full mirror)
  - **P2**: additive sync skipped when a real root was configured → run the sync so newly-found disk dirs land in `directory_tree`

### 7. Directory Numbering

- [ ] Any L1/L2 directory the skill creates carries a zero-padded 2-digit numeric prefix from `01`, sequential by sibling
  - **P1**: a created directory lacks the `NN ` prefix (or reuses/skips a number) → run `naming.py upsert --l1 <type>` (and `--l2 <type>`) to normalise; `upsert` enforces the convention automatically
  - **P2**: exempt dirs (`history`/`refer` in English, or their Chinese equivalents, and `99 Other`) appear numbered → these are intentionally exempt, no action

---

## QA Process

Run the checklist as a multi-round gate **before** delivering any filename.

```
Round 1: full scan of all check items
         (Extension → Type → Format → Version → Archive → Path)
    ├── tick each item, record every ❌
    ├── fix by P0 → P1 → P2 priority
    └── after fixes → Round 2
          ↓
Round 2: re-check
    ├── focus on previous ❌ items
    ├── check fixes introduced no new issue
    └── all pass → Round 3
          ↓
Round 3: final pass
    ├── all ✅ → deliver
    └── any P0/P1 ❌ → fix → restart from Round 1
```

### Judgment Rules

- **Pass**: 3 consecutive rounds with all P0/P1 cleared, P2 recorded.
- **Fail**: any unresolved P0/P1 in a round → fix, then **restart from Round 1**.
- **Block**: still failing after 5 rounds → emit a Blocking Report and pause.

---

## Self-Check Report Format

```markdown
## Self-Check Report · Round N · document-naming

### Passed
- Extension Validation ✅
- Type Matching ✅

### To Fix
- ❌ P0 Filename Format — missing author field, reject
- ⚠️ P2 Archive — multiple old versions could be consolidated

**Round verdict**: fail (1 P0 to fix)
P0: 1 | P1: 0 | P2: 1
Rounds run: 2 / 5
```

---

## Blocking Report Format

```markdown
## ⚠️ Blocking Report · document-naming

Self-check ran 5 rounds; the following still fail:

- ❌ P1 Type Matching — 2 documents could not resolve a tree type and
  auto-detect confirmation is unavailable
  Suggest: supply an explicit `--type` or confirm the proposed type

**Suggestion**: pause auto-fix; ask the user to confirm the type before continuing.
```

---

## Delivery Judgment

All P0/P1 resolved. P2 recorded in advisory notes. P0 residual → do not deliver.
