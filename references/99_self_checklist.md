# Quality Self-Checklist

Run after filename generation and before archiving. P0 must pass before output.

> This file is the QA checklist for document-naming. Numbered 99 as QA is the final gate before delivering names.

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
- [ ] Directory and type adapted to detected language
  - **P1**: Chinese document placed in English-named directory → switch to Chinese directory name
  - **P1**: English document placed in Chinese-named directory → switch to English directory name
- [ ] Type prefix resolved from `directory_tree` or kept as-is
  - **P1**: type matches no known prefix → check if fallback_dir_name is correct
  - **P2**: type could match multiple entries → document ambiguity

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

- [ ] Config sources loaded and merged correctly
  - **P0**: workspace_root not found → error with guidance
  - **P1**: workspace config file missing → fall back to config.json defaults
  - **P2**: unused config keys present → note

---

## Delivery Judgment

All P0/P1 resolved. P2 recorded in advisory notes. P0 residual → do not deliver.
