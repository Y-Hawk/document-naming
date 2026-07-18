# Workspace Reference

Shared by `document-naming`. Defines the **directory tree** (authoritative, auto-updated) and the directory numbering convention. The directory tree itself encodes the type mapping, so no separate mapping table is needed.

> This file is the **single source of truth** for the workspace directory tree.
> It is parsed and **auto-updated** by `scripts/naming.py` (`upsert` command) whenever a new L1/L2 directory is created. Do not hand-edit the JSON block unless you are fixing a parse error — prefer letting the skill manage it.

---

## Workspace Root

Absolute root directory under which all L1/L2 directories are created. This is the authoritative root location (see SKILL.md §Workspace Root Resolution): the path below is used directly; if empty, the skill falls back to system user root/DocumentSpace (created on the fly, never the bare Desktop / user root).

The current context root:

`C:/Users/admin.DESKTOP-FETRK5E/Desktop/内容创作专家`

---

## Workspace Config

Workspace-level runtime settings. These are the **authoritative** values —
`naming.py` reads them from this section (the SKILL.md `### Configuration`
table no longer carries them). The directory tree source is fixed at
`references/workspace.md` itself (see `references/rules.md`).

| Key                 | Value     | Description                                                  |
| ------------------- | --------- | ------------------------------------------------------------ |
| `archive_dir_name`  | `history` | Sub-directory for archived (non-final) old versions          |
| `refer_dir_name`    | `refer`   | Sub-directory for `.refer` old versions                     |

> Change a value here and `naming.py` picks it up on the next run — no script
> edit needed.

---

## Directory Tree

The machine-readable, authoritative directory layout. `naming.py` reads and writes this block.

```json
{
  "01": {
    "name": "01 Plan",
    "type": "Plan",
    "sub": {
      "01": {
        "name": "01 Operations Plan"
      },
      "02": {
        "name": "02 Topic Plan"
      },
      "03": {
        "name": "03 Skill Plan"
      },
      "99": {
        "name": "99 Reference Docs"
      }
    }
  },
  "02": {
    "name": "02 Question Bank",
    "type": "Question Bank",
    "sub": {}
  },
  "03": {
    "name": "03 Article",
    "type": "Article",
    "sub": {
      "01": {
        "name": "01 WorkBuddy"
      },
      "02": {
        "name": "02 AI's Past and Present"
      },
      "03": {
        "name": "03 AI Career Series"
      },
      "99": {
        "name": "99 Other"
      },
      "04": {
        "name": "04 Intro Course"
      }
    }
  },
  "04": {
    "name": "04 Standard",
    "type": "Standard",
    "sub": {
      "history": {
        "name": "history"
      },
      "01": {
        "name": "01 OpenClaw Config"
      }
    }
  },
  "05": {
    "name": "05 Asset",
    "type": "Asset",
    "sub": {
      "01": {
        "name": "01 Article Illustrations"
      },
      "02": {
        "name": "02 Reference List"
      },
      "99": {
        "name": "99 Other"
      }
    }
  },
  "98": {
    "name": "98 Opinion",
    "type": "Opinion",
    "sub": {
      "01": {
        "name": "01 Skill"
      },
      "02": {
        "name": "02 Article"
      },
      "03": {
        "name": "03 Plan"
      },
      "04": {
        "name": "04 Script"
      }
    }
  },
  "99": {
    "name": "99 Other",
    "type": "Other",
    "sub": {
      "01": {
        "name": "01 PMP"
      },
      "02": {
        "name": "02 Resignation"
      },
      "03": {
        "name": "03 Resume"
      },
      "04": {
        "name": "04 Music"
      }
    }
  }
}
```

> **Depth cap: two levels only.** The tree is intentionally capped at L1 + L2. L2 entries carry **no `sub`** — the skill never creates a third level. (`upsert` only operates on L1/L2, so a third level cannot be produced.)

### Schema

| Field | Meaning |
| ----- | ------- |
| **L1 key** | The **zero-padded number only**, e.g. `03`, `98`, `99`. (Not the descriptive name — see §Directory Numbering Convention.) |
| **L1 `name`** | Full L1 directory name `NN English name`, e.g. `03 Article`. |
| **L1 `type`** | Filename type prefix — the descriptive name **with the numeric prefix stripped** (e.g. `03 Article` → `Article`). **This is the only field that defines a document's type.** |
| **L1 `sub`** | Dict of L2 directories (the only nesting level permitted). `{}` = no L2. |
| **L2 key** | The **zero-padded number only**, e.g. `01`, `02`, `99`. (Not the descriptive name — see §Directory Numbering Convention.) |
| **L2 `name`** | Full L2 directory name `NN English name` for numbered dirs (e.g. `01 WorkBuddy`); the **original un-numbered name** for pre-existing legacy dirs (e.g. `Skill`, `PMP`). |
| legacy L2 | Pre-existing, un-numbered L2 dirs are **not** renamed on disk; their `name` keeps the original (`Skill`, `PMP`), but they are assigned an auto-filled numeric **key** so the tree stays consistent. |

### Type Resolution

The directory tree **is** the type mapping — each L1 entry's `type` field already encodes the filename prefix, so no separate mapping table is needed. Rules when resolving a document's type:

- **Type = first-level directory ONLY.** A document's type is determined **solely by its L1 directory** (the `type` field). The L2 directory is a **sub-category / save location**, **never** a document type and **never** part of the filename type prefix.
- **Match on first-level directory only.** Look up the L1 directory's `type` field; do **not** descend into L2 for type matching, and do **not** treat an L2 name as a candidate type.
- **Strip the numeric prefix for the filename.** The type prefix used in the generated filename is the L1 directory name **with its numeric prefix removed** — e.g. `03 Article/` → type `Article`; `01 Plan/` → type `Plan`.
- **Unmatched stays as-is.** Files outside all known directories keep their original prefix — never error.

> **Language note**: the tree's `type` values (e.g. `Article`, `Plan`). Resolve the type against this tree for **every** document regardless of the document's language — the detected language governs the **title and content wording**, not the directory structure or the type prefix. Do not create parallel English-named L1 directories; reuse the existing L1 that matches the concept (e.g. an English article → `03 Article`, prefix `Article`).

---

## Directory Numbering Convention

**MANDATORY** for any first-level (L1) or second-level (L2) directory the skill **creates by default** under the workspace.

### Rule

1. Every L1 / L2 directory name MUST begin with a **zero-padded 2-digit number** (`01`, `02`, `03`, …), separated from the descriptive name by a single space: `06 Tool/`, `04 Case Library/`.
2. **Numbering starts at `01`** and increments by 1 for each sibling, in creation / visual-sort order.
3. To pick the next number, read the existing siblings in the same parent directory and take `max(existing numbers) + 1`. Do not reuse or skip numbers.
4. The numeric prefix is **part of the directory name only** — it is stripped before becoming the filename type prefix (see §Type Resolution above).
5. Sub-directories under a numbered parent inherit the same numbering scheme independently (their sequence is local to that parent).

### Exempt directories (no numeric prefix required)

| Directory | Reason |
| --------- | ------ |
| `history/`   | Archive dir — name set in `## Workspace Config` (`archive_dir_name`) |
| `refer/`     | Reference dir — name set in `## Workspace Config` (`refer_dir_name`) |
| `99 Other/`   | Reserved fallback L1 — fixed `99_` prefix |

### Reserved prefixes (never auto-assigned to a *new* directory)

- L1: `98` and `99` are reserved (`98 Opinion`, `99 Other`).
- L2: `99` is reserved as the "Other" catch-all.

### Examples

| Parent            | New L2 needed        | Generated name     | Filename type |
| ----------------- | -------------------- | ------------------ | ------------- |
| `03 Article/` (subs end at `03 …`) | a new series `Overseas` | `04 Overseas/`    | `Overseas`        |
| workspace root (L1 end at `05 Asset`) | a new category `Data` | `06 Data/` | `Data`  |
| `05 Asset/` (subs `01…`,`02…`,`99…`) | a new asset group `Video` | `03 Video/` | `Video` |

> Existing directories that predate this convention (e.g. `98 Opinion/Skill`, `99 Other/PMP`) are **not** retroactively renumbered — the rule governs future default creation only.

> The `upsert` command in `naming.py` enforces all of the above automatically: it computes the next number, creates the L1 key as the bare number (full `NN name` stored in its `name` field) and the L2 key as the bare number (full `NN name` stored in its `name` field — or the original un-numbered name for legacy dirs), then writes the tree back to this file.
