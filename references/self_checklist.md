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
  - **P2**: confirmation prompt omitted the "auto-creates directory + syncs workspace.md" notice → re-prompt with full notice

### 3. Filename Format

- [ ] Filename follows `{type}_{title}_{date}_v{x.y.z}_{author}.{ext}` format
  - **P0**: missing required fields (type/date/author) → reject
  - **P1**: version format incorrect → correct to semver
  - **P2**: title contains special characters → suggest sanitization

### 4. Version Management

- [ ] Version bump (major/minor/patch) correctly applied
  - **P1**: bump type doesn't match change → suggest correct level
  - **P2**: version string format edge case → normalize

### 5. Archive

- [ ] Old version archived to `archive_dir_name` directory
  - **P0**: archive via move, not copy (data loss risk if copy+delete)
  - **P1**: archive directory doesn't exist → create it
  - **P2**: multiple old versions could be consolidated

### 6. Path & Cross-Reference

- [ ] Config loaded from SKILL.md `## Configuration` (single source); tree loaded from `references/workspace.md`
  - **P0**: SKILL.md Configuration table missing/unparseable → error with guidance
  - **P1**: workspace.md `## Directory Tree` JSON block unparseable → fix or rebuild the block
  - **P2**: directory created but not synced to workspace.md → run `naming.py upsert` to sync

### 7. Directory Numbering

- [ ] Any L1/L2 directory the skill creates carries a zero-padded 2-digit numeric prefix from `01`, sequential by sibling
  - **P1**: a created directory lacks the `NN ` prefix (or reuses/skips a number) → run `naming.py upsert --l1 <type>` (and `--l2 <type>`) to normalise; `upsert` enforces the convention automatically
  - **P2**: exempt dirs (`history`, `refer`, `99 Other`) appear numbered → these are intentionally exempt, no action

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
