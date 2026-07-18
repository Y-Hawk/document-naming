#!/usr/bin/env python3
"""Document naming tool — generate, bump, archive compliant filenames, and
manage the workspace directory tree.

Config source: SKILL.md `### Configuration` table (author / extension /
whitelist only). Workspace-level settings (root, archive/refer directory names)
live in `references/workspace.md`.

Format: see references/rules.md

Commands:
    generate  <title> <ext> --type <type> --author <author>
              [--date YYYYMMDD] [--suffix final|refer]
    bump      <filename> <major|minor|patch>
    archive   <file_path>
    tree                                   # print current directory_tree
    root                                   # resolve workspace root
                                           # (config → context → default)
    upsert    --l1 <type> [--l2 <type>]    # ensure L1/L2 exists (01-numbering),
                                           # write back to workspace.md
"""

import json, re, sys
from datetime import date
from pathlib import Path


# =============================================================================
#  Paths
# =============================================================================

def _skill_root() -> Path:
    """Resolve skill root directory (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent

_SKILL_ROOT = _skill_root()

# Reserved numeric prefixes (never auto-assigned to a *new* directory)
_L1_RESERVED_MAX = 98   # 98 Opinion / 99 Other are reserved L1 buckets
_L2_RESERVED_MAX = 99   # 99 … is the reserved "Other" catch-all at L2
_FALLBACK_TYPE = "Other"  # used when no type can be resolved

# System user root directory per platform — the base under
# which the default `DocumentSpace` folder is created by the skill. `Path.home()`
# resolves the *active* one at runtime; this table is documentation + explicit
# reference so the supported roots are listed in one place.
_SYSTEM_USER_ROOTS = {
    "windows": "C:/Users/<username>",
    "macos":   "/Users/<username>",
    "linux":   "/home/<username>",
}


# =============================================================================
#  Config loading — SKILL.md Configuration table (single source)
# =============================================================================

def _read_skill_config() -> dict:
    """Parse the `### Configuration` (H3) table from SKILL.md.

    Returns a dict of raw string values (keys are the config variable names).
    Soft-fails to {} on any error.

    The table lives under the `## Preconditions` H2 as an H3 heading
    (`### Configuration`), so the section regex matches `#{2,3}` headings and
    stops at the next H2/H3. Only lowercase config keys are captured, which
    also excludes the table header row (`Key`/`Value`).
    """
    try:
        text = (_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return {}

    result = {}
    sec = re.search(
        r"^### Configuration\b(.*?)(?=^#{2,3} |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if not sec:
        return result

    for m in re.finditer(
        r"^\|\s*`?([a-z_]+)`?\s*\|\s*([^|]+?)\s*\|", sec.group(1), re.MULTILINE
    ):
        # Strip the surrounding backticks that wrap cell values in the table.
        val = m.group(2).strip().strip("`")
        # The `*(empty)*` marker in the table means "unset" — normalise to "".
        result[m.group(1)] = "" if val == "*(empty)*" else val
    return result


# =============================================================================
#  Directory tree loading / writing — references/workspace.md JSON block
# =============================================================================

# Fixed convention: the directory tree / workspace settings always live in this
# file. Documented in references/rules.md (the `workspace_doc` SKILL.md config
# key was removed).
_WORKSPACE_DOC = "references/workspace.md"


def _workspace_doc_path() -> Path:
    """Path to the authoritative workspace doc (references/workspace.md)."""
    return _SKILL_ROOT / _WORKSPACE_DOC


# Matches the `## Workspace Config` section and captures its key/value table.
_WORKSPACE_CFG_RE = re.compile(
    r"^## Workspace Config\b(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)


def _parse_workspace_config() -> dict:
    """Read workspace-level settings from `references/workspace.md`
    `## Workspace Config` section (authoritative source for the archive/refer
    directory names). Returns {} on missing file / section.
    """
    try:
        text = _workspace_doc_path().read_text(encoding="utf-8")
    except OSError:
        return {}
    sec = _WORKSPACE_CFG_RE.search(text)
    if not sec:
        return {}
    result = {}
    for m in re.finditer(
        r"^\|\s*`?([a-z_]+)`?\s*\|\s*`?([^|`\n]+?)`?\s*\|",
        sec.group(1), re.MULTILINE,
    ):
        result[m.group(1)] = m.group(2).strip().strip("`")
    return result


# Matches the `## Directory Tree` section and captures (group1) everything up
# to the opening ```json, and (group2) the JSON body. Tolerates an intro
# paragraph between the heading and the code fence.
_TREE_BLOCK_RE = re.compile(r"(## Directory Tree\b.*?)```json\s*(.*?)\s*```", re.DOTALL)


def _parse_workspace_tree() -> dict:
    """Read the `## Directory Tree` JSON block from the workspace doc.

    Returns {} on missing file / missing block / JSON error.
    """
    try:
        text = _workspace_doc_path().read_text(encoding="utf-8")
    except OSError:
        return {}

    m = _TREE_BLOCK_RE.search(text)
    if not m:
        return {}
    try:
        return json.loads(m.group(2))
    except json.JSONDecodeError:
        return {}


def _write_workspace_tree(tree: dict) -> bool:
    """Rewrite the `## Directory Tree` JSON block in the workspace doc.

    Preserves any intro text before the code fence. Creates the section if
    absent. Returns True on success.
    """
    path = _workspace_doc_path()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    block_body = json.dumps(tree, ensure_ascii=False, indent=2)

    if _TREE_BLOCK_RE.search(text):
        new_text = _TREE_BLOCK_RE.sub(
            lambda m: m.group(1) + "```json\n" + block_body + "\n```", text, count=1
        )
    else:
        new_text = text.rstrip() + "\n\n## Directory Tree\n\n```json\n" + block_body + "\n```\n"

    path.write_text(new_text, encoding="utf-8")
    return True


def _load_config() -> dict:
    """Build the merged runtime config dict.

    Author/extension/whitelist come from SKILL.md `### Configuration` (single
    source). Archive/refer directory names come from the workspace doc
    `## Workspace Config` section. The directory tree comes from the workspace
    doc JSON block.
    """
    raw = _read_skill_config()
    ws_cfg = _parse_workspace_config()

    allowed = [e.lower().lstrip(".") for e in raw.get("allowed_extensions", "").split(",") if e.strip()]
    cfg = {
        "default_author": raw.get("default_author", "Unknown").strip(),
        "default_extension": raw.get("default_extension", "md").strip().lstrip(".").lower(),
        "allowed_extensions": allowed or ["md", "pptx", "xlsx", "docx", "pdf", "png", "mp4", "mp3"],
        "archive_dir_name": (ws_cfg.get("archive_dir_name") or "history").strip() or "history",
        "refer_dir_name": (ws_cfg.get("refer_dir_name") or "refer").strip() or "refer",
        "directory_tree": _parse_workspace_tree(),
    }
    return cfg


_config = _load_config()


def _cfg(key: str, default: str = "") -> str:
    """Read a merged config value, returning *default* if key is absent."""
    return str(_config.get(key, default))


def _allowed_extensions() -> list[str]:
    """Return the allowed_extensions whitelist from merged config (lowercased)."""
    exts = _config.get("allowed_extensions")
    if isinstance(exts, list) and exts:
        return [e.lower().lstrip(".") for e in exts if isinstance(e, str)]
    return ["md", "pptx", "xlsx", "docx", "pdf", "png", "mp4", "mp3"]


# =============================================================================
#  Workspace root resolution — 2-tier: context (workspace.md) → default
# =============================================================================

def _default_workspace_root() -> Path:
    """The last-resort root: `<system user root>/DocumentSpace`.

    The "system user root" is the OS user home directory (`Path.home()`), which
    differs per platform:
      - Windows: C:\\Users\\<username>
      - macOS:   /Users/<username>
      - Linux:   /home/<username>
    `Path.home()` resolves the correct one automatically. Never the bare
    Desktop — a dedicated DocumentSpace folder avoids mixing with unrelated
    items. (The `default_workspace_root` SKILL.md config key was removed; this
    default is now fixed — see `references/rules.md`.)
    """
    return Path.home() / "DocumentSpace"


def _parse_workspace_root_from_doc() -> str:
    """Read the context root from the workspace doc `## Workspace Root` section.

    Returns the first back-tick-wrapped path in that section, or "" if the
    section / file is absent.
    """
    try:
        text = _workspace_doc_path().read_text(encoding="utf-8")
    except OSError:
        return ""
    sec = re.search(r"^## Workspace Root\b(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not sec:
        return ""
    m = re.search(r"`([^`\n]+)`", sec.group(1))
    return m.group(1).strip() if m else ""


def _resolve_workspace_root() -> dict:
    """Resolve the absolute workspace root through the 2-tier chain:

      1. context — workspace.md `## Workspace Root` section (authoritative)
      2. default — `<system user root>/DocumentSpace` (created if missing)

    Returns {"root": <abs path>, "source": "context|default",
             "created": bool}. Only the default tier ever creates a directory.
    There is no SKILL.md config override — set the root in workspace.md.
    """
    ctx = _parse_workspace_root_from_doc()
    if ctx:
        return {"root": str(Path(ctx)), "source": "context", "created": False}

    d = _default_workspace_root()
    created = not d.exists()
    d.mkdir(parents=True, exist_ok=True)
    return {"root": str(d), "source": "default", "created": created}


# =============================================================================
#  Filename regex — canonical format
# =============================================================================
#   $1  type       leading segment before first underscore
#   $2  title      free-form
#   $3  date       8-digit YYYYMMDD
#   $4  version    semantic version X.Y.Z (no leading v)
#   $5  suffix     optional .final or .refer (including leading dot), or None
#   $6  suffix keyword (final|refer) — internal, not exposed
#   $7  author     word characters only
#   $8  extension  file suffix after final dot

FILENAME_RE = re.compile(
    r"^([^_]+)_(.+)_(\d{8})_v(\d+\.\d+\.\d+)(\.(final|refer))?_(\w+)\.(\w+)$"
)


# =============================================================================
#  Internal helpers
# =============================================================================

def _sanitize(title: str) -> str:
    """Sanitise a title for use as a filename segment.

    1. Strip characters illegal on Windows: \\ / : * ? " < > |
    2. Remove all whitespace.
    3. Truncate to 30 characters max.
    4. Empty result → "untitled".
    """
    clean = re.sub(r'[\\/:*?"<>|]', "", title)
    clean = re.sub(r"\s+", "", clean)
    return clean[:30] or "untitled"


def _resolve_author(context_author: str = "") -> str:
    """Resolve author: caller context → config default_author → 'Unknown'."""
    if context_author and context_author.strip():
        return context_author.strip()
    fb = _cfg("default_author", "Unknown")
    return fb.strip() or "Unknown"


def _prefix_of(key: str) -> int | None:
    """Extract the leading zero-padded number from a directory key, else None."""
    head = key.split()[0] if key.split() else ""
    return int(head) if head.isdigit() else None


def _core_name(name: str) -> str:
    """Descriptive part of a directory name with the numeric prefix stripped.

    '03 Article' -> 'Article'; '01 WorkBuddy' -> 'WorkBuddy'; 'Skill' -> 'Skill'.
    Used to match a requested type against a directory's stored name.
    """
    parts = name.split(" ", 1)
    return parts[1] if len(parts) == 2 and parts[0].isdigit() else name


def _next_number(existing: list[int], reserved_max: int) -> int:
    """Next zero-padded number: max(usable) + 1, usable = 1..reserved_max-1."""
    usable = [n for n in existing if 1 <= n < reserved_max]
    return (max(usable) if usable else 0) + 1


# =============================================================================
#  Core API
# =============================================================================

def parse_filename(filename: str) -> dict | None:
    """Parse a compliant filename into structured fields.

    Returns dict with keys: type, title, date, version, suffix, author, ext.
    Returns None if filename does not match the canonical format.
    """
    m = FILENAME_RE.match(filename)
    if not m:
        return None
    return {
        "type":    m.group(1),
        "title":   m.group(2),
        "date":    m.group(3),
        "version": m.group(4),
        "suffix":  m.group(5) or "",
        "author":  m.group(7),
        "ext":     m.group(8),
    }


def generate_name(
    title: str,
    ext: str,
    file_type: str = "",
    author: str = "",
    date_str: str = "",
    suffix: str = "",
) -> dict:
    """Generate a compliant filename for a **new** document. No disk I/O.

    Returns: {"name", "type", "title", "date", "version", "suffix", "author", "ext"}
    Raises ValueError if extension not in allowed_extensions whitelist.
    """
    e = ext.lstrip(".").lower()
    allowed = _allowed_extensions()
    if e not in allowed:
        raise ValueError(
            f"Extension '{e}' not in allowed_extensions whitelist {allowed}. "
            f"Refusing execution — hard gate validation failed."
        )

    prefix = file_type.strip() or _FALLBACK_TYPE
    t = _sanitize(title)
    d = date_str or date.today().strftime("%Y%m%d")
    a = _resolve_author(author)
    v = "1.0.0"
    s = f".{suffix}" if suffix in ("final", "refer") else ""

    name = f"{prefix}_{t}_{d}_v{v}{s}_{a}.{e}"
    return {
        "name":    name,
        "type":    prefix,
        "title":   t,
        "date":    d,
        "version": f"v{v}",
        "suffix":  s,
        "author":  a,
        "ext":     e,
    }


def bump_version(filename: str, level: str = "patch") -> dict:
    """Bump version number and refresh date to today.

    Reconstructs the filename from parsed parts — no string-replace ambiguity.
    Raises ValueError if filename is not compliant.
    """
    p = parse_filename(filename)
    if not p:
        raise ValueError(f"Non-compliant filename: {filename}")

    major, minor, patch = map(int, p["version"].split("."))
    if level == "major":
        major += 1; minor = 0; patch = 0
    elif level == "minor":
        minor += 1; patch = 0
    else:
        patch += 1

    new_ver = f"v{major}.{minor}.{patch}"
    today = date.today().strftime("%Y%m%d")

    new_name = (
        f"{p['type']}_{p['title']}_{today}_{new_ver}{p['suffix']}"
        f"_{p['author']}.{p['ext']}"
    )

    return {
        "old_name":    filename,
        "new_name":    new_name,
        "old_version": f"v{p['version']}",
        "new_version": new_ver,
        "suffix":      p["suffix"],
    }


def archive_old_version(file_path: str | Path) -> Path | None:
    """Move a file into the appropriate archive sub-directory.

    Routing by version suffix:
      (none)  → <source_parent>/<archive_dir_name>/
      .refer  → <source_parent>/<refer_dir_name>/
      .final  → NOT moved (returns None without error)

    Target directory is created if missing. Name collisions resolved
    by appending _1, _2, ... before the extension.

    Returns destination Path on success, or None if:
      - source file does not exist
      - suffix is .final (no move needed)
    """
    src = Path(file_path)
    if not src.exists():
        return None

    parsed = parse_filename(src.name)

    if parsed and parsed["suffix"] == ".final":
        return None

    if parsed and parsed["suffix"] == ".refer":
        dir_name = _cfg("refer_dir_name", "refer")
    else:
        dir_name = _cfg("archive_dir_name", "history")

    archive_dir = src.parent / dir_name
    archive_dir.mkdir(exist_ok=True)

    dest = archive_dir / src.name
    if dest.exists():
        n = 1
        while dest.exists():
            dest = archive_dir / f"{src.stem}_{n}{src.suffix}"
            n += 1

    src.rename(dest)
    return dest


# =============================================================================
#  Directory tree management
# =============================================================================

def upsert_dir(l1_type: str, l2_type: str = "") -> dict:
    """Ensure an L1 (and optional L2) directory exists in the workspace tree.

    - If the directory already exists (matched by type), returns its key unchanged.
    - Otherwise creates it with a zero-padded 2-digit numeric prefix
      starting from `01`, sequential by sibling (forced numbering convention),
      and writes the updated tree back to the workspace doc.

    Args:
        l1_type: descriptive L1 type, e.g. "Data" (without the numeric prefix)
        l2_type: descriptive L2 type, e.g. "Case Library"

    L1 key uses the bare NUMBER only (e.g. "06"); L2 key also uses the NUMBER
    only (e.g. "04"); in both cases the full "NN name" is stored in `name`.
    A document's type is resolved from the L1 `type` field — L2 is a
    sub-category, never a type.

    Returns: {"l1": "<key>", "l2": "<key>|null", "created": bool}
    """
    tree = _parse_workspace_tree()
    created = False

    # ---- L1 ----
    # L1 key is the bare number (e.g. "03"); the full "NN name" lives in `name`.
    # A document's type is matched against the L1 `type` field (or the core of
    # its `name`) — L2 is a sub-category and is NEVER treated as a type.
    # Normalize the requested type: strip a leading "NN " prefix so that both
    # "Article" and "03 Article" resolve to the same L1.
    l1_core = _core_name(l1_type)
    l1_key = None
    for k, v in tree.items():
        if (v.get("type") == l1_core
                or _core_name(v.get("name", k)) == l1_core
                or k == l1_core):
            l1_key = k
            break
    if l1_key is None:
        nums = [_prefix_of(k) for k in tree if _prefix_of(k) is not None]
        n = _next_number(nums, _L1_RESERVED_MAX)
        l1_key = f"{n:02d}"
        tree[l1_key] = {"name": f"{n:02d} {l1_type}", "type": l1_type, "sub": {}}
        created = True

    result = {"l1": l1_key, "l2": None, "created": created}

    # ---- L2 ----
    # L2 key is the zero-padded NUMBER only (e.g. "01"); the full directory
    # name "01 WorkBuddy" is stored in the entry's `name` field. Legacy,
    # un-numbered L2 dirs keep their original name as both key and name.
    if l2_type:
        l2_core = _core_name(l2_type)
        subs = tree[l1_key].setdefault("sub", {})
        l2_key = None
        for k, v in subs.items():
            nm = v.get("name", k)
            if (_core_name(nm) == l2_core or nm == l2_type or k == l2_type):
                l2_key = k
                break
        if l2_key is None:
            nums = [_prefix_of(k) for k in subs if _prefix_of(k) is not None]
            n = _next_number(nums, _L2_RESERVED_MAX)
            l2_key = f"{n:02d}"
            subs[l2_key] = {"name": f"{n:02d} {l2_type}"}
            created = True
        result["l2"] = l2_key

    result["created"] = created
    _write_workspace_tree(tree)
    return result


# =============================================================================
#  CLI — thin wrappers over Core API
# =============================================================================
# All output is JSON. All errors are {"error": "..."} + exit(1).

def _err(msg: str, code: int = 1) -> None:
    """Print JSON error and exit."""
    print(json.dumps({"error": msg}))
    sys.exit(code)


def _parse_flags(args: list[str], mapping: dict[str, str]) -> dict[str, str]:
    """Parse --flag value pairs; unknown flags silently skipped."""
    result = {}
    i = 0
    while i < len(args):
        key = mapping.get(args[i])
        if key and i + 1 < len(args):
            result[key] = args[i + 1]
            i += 2
        else:
            i += 1
    return result


def _cmd_generate() -> None:
    if len(sys.argv) < 4:
        _err("Usage: naming.py generate <title> <ext> "
             "--type <type> --author <author> [--date YYYYMMDD] [--suffix final|refer]")

    opts = _parse_flags(sys.argv[4:], {
        "--type":   "file_type",
        "--author": "author",
        "--date":   "date_str",
        "--suffix": "suffix",
    })

    try:
        result = generate_name(
            sys.argv[2], sys.argv[3],
            opts.get("file_type", ""),
            opts.get("author", ""),
            opts.get("date_str", ""),
            opts.get("suffix", ""),
        )
    except ValueError as e:
        _err(str(e))

    print(json.dumps(result, ensure_ascii=False))


def _cmd_bump() -> None:
    if len(sys.argv) < 4:
        _err("Usage: naming.py bump <filename> <major|minor|patch>")

    level = sys.argv[3]
    if level not in ("major", "minor", "patch"):
        _err(f"Invalid bump level: '{level}'. Use major/minor/patch.")

    try:
        print(json.dumps(bump_version(sys.argv[2], level), ensure_ascii=False))
    except ValueError as e:
        _err(str(e))


def _cmd_archive() -> None:
    if len(sys.argv) < 3:
        _err("Usage: naming.py archive <file_path>")

    src = Path(sys.argv[2])
    if not src.exists():
        _err(f"File not found: {src}")

    dest = archive_old_version(src)
    if dest:
        print(json.dumps({"archived": str(src), "to": str(dest)}, ensure_ascii=False))
    else:
        print(json.dumps(
            {"archived": str(src), "to": None, "note": ".final — not moved"},
            ensure_ascii=False,
        ))


def _cmd_tree() -> None:
    print(json.dumps(_parse_workspace_tree(), ensure_ascii=False, indent=2))


def _cmd_root() -> None:
    print(json.dumps(_resolve_workspace_root(), ensure_ascii=False))


def _cmd_upsert() -> None:
    opts = _parse_flags(sys.argv[2:], {"--l1": "l1", "--l2": "l2"})
    if not opts.get("l1"):
        _err("Usage: naming.py upsert --l1 <type> [--l2 <type>]")
    print(json.dumps(
        upsert_dir(opts["l1"], opts.get("l2", "")),
        ensure_ascii=False,
    ))


def main() -> None:
    cmds = {
        "generate": _cmd_generate,
        "bump":     _cmd_bump,
        "archive":  _cmd_archive,
        "tree":     _cmd_tree,
        "root":     _cmd_root,
        "upsert":   _cmd_upsert,
    }

    if len(sys.argv) < 2:
        _err(f"Usage: naming.py <{'|'.join(cmds)}> [args...]")

    cmd = sys.argv[1]
    if cmd in cmds:
        cmds[cmd]()
    else:
        _err(f"Unknown command: '{cmd}'")


if __name__ == "__main__":
    main()
