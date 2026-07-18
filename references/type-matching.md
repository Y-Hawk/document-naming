# Type Matching
**Applies to: `create`.**

Resolves the type prefix for the filename. Data source: the `directory_tree` parsed from `references/workspace.md` (the `## Directory Tree` JSON block).

---

## Prerequisite

**Merged config** = values parsed by `naming.py` from the SKILL.md `## Configuration` table. The `directory_tree` is read separately from `references/workspace.md`.

**Hard gate (extension)**: any extension not in `allowed_extensions` is refused before any step. Rule + whitelist → `references/rules.md` §Extension.

---

## Type Resolution

| Scenario | Action |
|----------|--------|
| Caller type matches a known type prefix | Normalize to matched prefix (mapped L1 directory) |
| Caller type matches no known prefix | Keep caller type (no error) |
| Caller provides no type | **Auto-detect from content** — see SKILL.md §Auto-Detect Flow. Propose a type, confirm with user (timeout → auto-execute), then create the directory and sync `references/workspace.md` via `naming.py upsert` |

### Auto-detect (no type provided)

1. Read the document's title + body.
2. Infer the best-fitting L1 type from the existing `directory_tree` (e.g. `Plan` / `Article` / `Question Bank` / `Asset` / `Standard` / `Opinion`); if nothing fits, propose `Other`.
3. Prompt the user to confirm or correct the proposed type. State that confirming auto-creates the directory and updates the workspace doc.
4. On confirmation **or timeout** (no response) → auto-execute:
   - `naming.py upsert --l1 <type>` → creates the L1 with forced `01` numbering and writes it back to `references/workspace.md`.
   - Create the directory on disk.
5. Use the resolved type as the filename prefix.

### Language adaptation

- Detect the document's primary language from title/content (do **not** assume English).
- The detected language governs the **title and content wording** — **not** the directory structure or the type prefix.
- Resolve the type against the `directory_tree` (its `type` values) for **every** document. Do **not** create parallel English-named L1 directories; reuse the existing L1 that matches the concept (e.g. an English article → `03 Article`, prefix `Article`). If a genuinely new concept appears, create it under the tree via `upsert`.
- The numeric prefix is language-neutral and always applied per the numbering convention.
