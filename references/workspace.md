# Workspace Reference

Shared by `document-naming`. Documents the **directory-tree schema**, the
**type-resolution rules**, and the **directory numbering convention**. The tree
itself encodes the type mapping, so no separate mapping table is needed.

> The real on-disk folders are Chinese-named; the examples below use English
> folder names for readability. The authoritative layout is defined in the
> skill's JSON configuration.

---

## Directory Schema

### Schema

| Field | Meaning |
| ----- | ------- |
| **L1 key** | The **zero-padded number only**, e.g. `03`, `98`, `99`. (Not the descriptive name — see §Directory Numbering Convention.) |
| **L1 `name`** | Full L1 directory name `NN name`, e.g. `03 Article`. |
| **L1 `type`** | Filename type prefix — the descriptive name **with the numeric prefix stripped** (e.g. `03 Article` → `Article`). **This is the only field that defines a document's type.** |
| **L1 `sub`** | Dict of L2 directories (the only nesting level permitted). `{}` = no L2. |
| **L2 key** | The **zero-padded number only**, e.g. `01`, `02`, `99`. (Not the descriptive name — see §Directory Numbering Convention.) |
| **L2 `name`** | Full L2 directory name `NN name` for numbered dirs (e.g. `01 WorkBuddy`); the **original un-numbered name** for pre-existing legacy dirs. |
| legacy L2 | Pre-existing, un-numbered L2 dirs are **not** renamed on disk; their `name` keeps the original, but they are assigned an auto-filled numeric **key** so the tree stays consistent. |

### Type Resolution

The directory tree **is** the type mapping — each L1 entry's `type` field already
encodes the filename prefix, so no separate mapping table is needed. Rules when
resolving a document's type:

- **Type = first-level directory ONLY.** A document's type is determined **solely by its L1 directory** (the `type` field). The L2 directory is a **sub-category / save location**, **never** a document type and **never** part of the filename type prefix.
- **Match on first-level directory only.** Look up the L1 directory's `type` field; do **not** descend into L2 for type matching, and do **not** treat an L2 name as a candidate type.
- **Strip the numeric prefix for the filename.** The type prefix used in the generated filename is the L1 directory name **with its numeric prefix removed** — e.g. `03 Article/` → type `Article`.
- **Unmatched stays as-is.** Files outside all known directories keep their original prefix — never error.

> **Language note**: resolve the type against this tree for **every** document regardless of the document's language — the detected language governs the **title and content wording**, not the directory structure or the type prefix. Do not create parallel English-named L1 directories; reuse the existing L1 that matches the concept.

---

## Directory Numbering Convention

**MANDATORY** for any first-level (L1) or second-level (L2) directory the skill
**creates by default** under the workspace.

### Rule

1. Every L1 / L2 directory name MUST begin with a **zero-padded 2-digit number** (`01`, `02`, `03`, …), separated from the descriptive name by a single space: `06 Tools/`, `04 Case Library/`.
2. **Numbering starts at `01`** and increments by 1 for each sibling, in creation / visual-sort order.
3. To pick the next number, read the existing siblings in the same parent directory and take `max(existing numbers) + 1`. Do not reuse or skip numbers.
4. The numeric prefix is **part of the directory name only** — it is stripped before becoming the filename type prefix (see §Type Resolution above).
5. Sub-directories under a numbered parent inherit the same numbering scheme independently (their sequence is local to that parent).
6. **Depth cap: two levels only.** The tree is intentionally capped at L1 + L2. L2 entries carry **no `sub`** — the skill never creates a third level. (`upsert` only operates on L1/L2, so a third level cannot be produced.)

### Exempt directories (no numeric prefix required)

| Directory | Reason |
| --------- | ------ |
| `history/` / `refer/` | Archive / reference dir — language-matched name, created at archive time (see `references/file-archive.md`) |
| `99 Other/` | Reserved fallback L1 — fixed `99_` prefix |

### Reserved prefixes (never auto-assigned to a *new* directory)

- L1: `98` and `99` are reserved (`98 Opinion`, `99 Other`).
- L2: `99` is reserved as the "Other" catch-all.

### Examples

| Parent | New L2 needed | Generated name | Filename type |
| ------ | ------------- | -------------- | ------------- |
| `03 Article/` (subs end at `06 …`) | a new series `Overseas` | `07 Overseas/` | `Article` (L1 type — L2 never changes the prefix) |
| workspace root (L1 end at `05 Assets`) | a new category `Data` | `06 Data/` | `Data` |

> Existing directories that predate this convention are **not** retroactively renumbered — the rule governs future default creation only.

> The `upsert` command in `naming.py` enforces all of the above automatically: it computes the next number, creates the L1 key as the bare number (full `NN name` stored in its `name` field) and the L2 key as the bare number (full `NN name` in its `name`, or the original un-numbered name for legacy dirs), then writes the tree back to the local config.
