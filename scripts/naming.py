#!/usr/bin/env python3
"""Document naming tool — generate, bump, archive compliant filenames, and
manage the workspace directory tree.

Config source: config.json (baseline) + config.local.json (machine-local
override) at the skill root. config.local.json wins key-by-key and receives all
runtime writes (directory-tree updates), so a remote sync that overwrites the
shared config.json never clobbers the local workspace_root / directory_tree.
Archive / refer folder names are NOT config — they are resolved at archive time
by the document's language (Chinese title → 历史版本/参考备份, else history/refer).

Format: see references/rules.md

Commands:
    generate  <title> <ext> --type <type> --author <author>
              [--date YYYYMMDD] [--suffix final|refer]
    bump      <filename> <major|minor|patch>
    archive   <file_path>
    tree                                   # print current directory_tree
    root                                   # resolve workspace root
                                           # (config.local/config.json → default)
    upsert    --l1 <type> [--l2 <type>]    # ensure L1/L2 exists (01-numbering),
                                           # write back to config.local.json
    scan      [--apply]                    # sync L1/L2 dirs on disk into the
                                           # tree (rules 1-4); --apply writes
                                           # to config.local.json
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
_FALLBACK_TYPE = "其它"  # fallback L1 bucket (99 其它) — used when no type can be resolved

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
#  Config loading — config.json (baseline) + config.local.json (local override)
# =============================================================================
#
#  Two JSON files at the skill root manage all runtime configuration:
#    - config.json        Baseline; may be committed / remotely managed. Holds
#                         the shared defaults (author / extension / whitelist)
#                         plus a snapshot of workspace_root + directory_tree.
#    - config.local.json  Machine-specific overrides (git-ignored). Holds this
#                         machine's workspace_root + directory_tree. It wins,
#                         key-by-key, over config.json — so a remote sync that
#                         overwrites config.json never clobbers the local
#                         root / tree.
#
#  All runtime writes (scan / upsert updating the tree) target config.local.json
#  only, keeping the live machine state out of the shared baseline.

_CONFIG_JSON = "config.json"
_CONFIG_LOCAL_JSON = "config.local.json"
_DEFAULT_ALLOWED = ["md", "pptx", "xlsx", "docx", "pdf", "png", "mp4", "mp3"]


def _config_path() -> Path:
    """Path to the baseline config (config.json)."""
    return _SKILL_ROOT / _CONFIG_JSON


def _config_local_path() -> Path:
    """Path to the machine-local override config (config.local.json)."""
    return _SKILL_ROOT / _CONFIG_LOCAL_JSON


def _read_json(path: Path) -> dict:
    """Read a JSON object from *path*. Soft-fails to {} on any error."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _merged_raw() -> dict:
    """Merge config.json (baseline) with config.local.json (override).

    config.local.json wins key-by-key — any key it defines replaces the
    baseline value wholesale (the directory_tree is replaced, not deep-merged).
    """
    merged = dict(_read_json(_config_path()))
    merged.update(_read_json(_config_local_path()))
    return merged


# =============================================================================
#  Directory tree loading / writing — config.local.json (write target)
# =============================================================================

def _parse_workspace_tree() -> dict:
    """The merged directory tree (config.local.json overrides config.json)."""
    tree = _merged_raw().get("directory_tree", {})
    return tree if isinstance(tree, dict) else {}


def _write_workspace_tree(tree: dict) -> bool:
    """Persist the directory tree into config.local.json (machine-local).

    Reads the existing local file, updates only the `directory_tree` key, and
    writes it back — preserving any other local keys (e.g. workspace_root).
    Writes never touch config.json (the shared baseline), so remote management
    can overwrite that file safely. Returns True on success.
    """
    local = _read_json(_config_local_path())
    local["directory_tree"] = tree
    try:
        _config_local_path().write_text(
            json.dumps(local, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def _load_config() -> dict:
    """Build the merged runtime config dict from the two JSON files.

    Author / extension / whitelist come from the merged config (baseline
    overridden by local). workspace_root and directory_tree likewise merge, with
    config.local.json taking precedence. Archive/refer directory names are NOT
    config — they are resolved at archive time by the document language (see
    `archive_old_version`).
    """
    raw = _merged_raw()

    allowed = raw.get("allowed_extensions")
    if isinstance(allowed, str):
        allowed = [e for e in allowed.split(",") if e.strip()]
    if not isinstance(allowed, list) or not allowed:
        allowed = list(_DEFAULT_ALLOWED)
    allowed = [str(e).lower().lstrip(".") for e in allowed if str(e).strip()]

    return {
        "default_author": str(raw.get("default_author") or "Unknown").strip() or "Unknown",
        "default_extension": (str(raw.get("default_extension") or "md").strip().lstrip(".").lower() or "md"),
        "allowed_extensions": allowed or list(_DEFAULT_ALLOWED),
        "workspace_root": str(raw.get("workspace_root") or "").strip(),
        "directory_tree": _parse_workspace_tree(),
    }


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
#  Workspace root resolution — 2-tier: config (config.json/.local) → default
# =============================================================================

def _default_workspace_root() -> Path:
    """The last-resort root: `<system user root>/DocumentSpace`.

    The "system user root" is the OS user home directory (`Path.home()`), which
    differs per platform:
      - Windows: C:\\Users\\<username>
      - macOS:   /Users/<username>
      - Linux:   /home/<username>
    `Path.home()` resolves the correct one automatically.     Never the bare
    Desktop — a dedicated DocumentSpace folder avoids mixing with unrelated
    items. (This default is fixed — see `references/rules.md`.)
    """
    return Path.home() / "DocumentSpace"


def _configured_workspace_root() -> str:
    """Read the configured workspace root from the merged config
    (config.local.json overrides config.json). Returns "" if unset.
    """
    return str(_merged_raw().get("workspace_root") or "").strip()


def _resolve_workspace_root() -> dict:
    """Resolve the absolute workspace root through the 2-tier chain:

      1. config — `workspace_root` from the merged config (config.local.json
                  overrides config.json) — authoritative when non-empty
      2. default — `<system user root>/DocumentSpace` (created if missing)

    Returns {"root": <abs path>, "source": "config|default",
             "created": bool}. Only the default tier ever creates a directory.
    """
    ctx = _configured_workspace_root()
    if ctx:
        return {"root": str(Path(ctx)), "source": "config", "created": False}

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


# System / application-class directories that must never be processed
# (rule 3). Dot-prefixed dirs (e.g. `.obsidian`) are caught separately by name.
_APP_DIRS = {"Excalidraw", "node_modules", ".git", ".idea", ".vscode"}


def _classify_dir(name: str) -> str:
    """Classify a directory name for the root-scan sync (rules 3 & 4).

    Returns one of:
      "skip_dot"       — name starts with "." (system/app config) → rule 3
      "skip_app"       — known app-class dir (e.g. Excalidraw)    → rule 3
      "skip_unnumbered"— no numeric prefix, not a content category → rule 3
      "content"        — numbered content directory (process it)
    """
    if name.startswith("."):
        return "skip_dot"
    if name in _APP_DIRS:
        return "skip_app"
    if _prefix_of(name) is None:
        return "skip_unnumbered"
    return "content"


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


# Archive sub-directory names, resolved by the document's language (a fixed
# RULE, not config): a Chinese-titled document archives into Chinese-named
# folders; anything else uses the English names. See references/rules.md
# §Archive Directory Names and references/file-archive.md.
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_ARCHIVE_DIRS = {"zh": "历史版本", "en": "history"}
_REFER_DIRS = {"zh": "参考备份", "en": "refer"}


def _doc_lang(name: str) -> str:
    """Detect a document's language from its filename: any CJK char → 'zh',
    otherwise 'en'. Drives the language-matched archive / refer folder names.
    """
    return "zh" if _CJK_RE.search(name) else "en"


def archive_old_version(file_path: str | Path) -> Path | None:
    """Move a file into the appropriate archive sub-directory.

    Routing by version suffix; the folder NAME is chosen by the document's
    language (Chinese title → Chinese folder, else English):
      (none)  → <source_parent>/{历史版本|history}/
      .refer  → <source_parent>/{参考备份|refer}/
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

    lang = _doc_lang(src.name)
    if parsed and parsed["suffix"] == ".refer":
        dir_name = _REFER_DIRS[lang]
    else:
        dir_name = _ARCHIVE_DIRS[lang]

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
      and writes the updated tree back to config.local.json (only when a new
      directory was actually created).

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
    if created:                       # persist only when a directory was added
        _write_workspace_tree(tree)
    return result


def scan_workspace(apply: bool = False) -> dict:
    """Scan the resolved root and sync L1/L2 directories into the tree.

    Implements the root-scan sync rules:
      1) number per convention — existing disk numbers are preserved as-is
      2) mirror the directory tree from the real disk (add / update / remove)
      3) skip dot-prefixed dirs (`.obsidian`) and system/app-class dirs
         (`Excalidraw`, …) — never processed
      4) only L1/L2 — L3+ directories are reported as excluded, never added

    The tree is rebuilt to **mirror** the disk exactly: every numbered content
    L1/L2 directory on disk is reflected, and any tree entry that no longer
    exists on disk is removed (the tree is functional data that must track the
    real folders). The `history` / `refer` exempt archive dirs are never added
    (they are L3+ and created at archive time).

    Args:
        apply: when True, write the mirrored tree back to config.local.json.
               when False (default), only report what *would* change.

    Returns a report dict: root, added, updated, removed, skipped, l3_excluded.
    """
    root = Path(_resolve_workspace_root()["root"])
    if not root.exists():
        return {"error": f"workspace root not found: {root}"}

    old = _parse_workspace_tree()
    tree: dict = {}
    added: list[str] = []
    updated: list[str] = []
    skipped: list[list[str]] = []
    l3_excluded: list[str] = []

    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if _classify_dir(d.name) != "content":
            skipped.append([d.name, _classify_dir(d.name)])
            continue
        l1_num = f"{_prefix_of(d.name):02d}"
        tree[l1_num] = {"name": d.name, "type": _core_name(d.name), "sub": {}}
        subs = tree[l1_num]["sub"]
        for s in sorted(d.iterdir()):
            if not s.is_dir():
                continue
            if _classify_dir(s.name) != "content":
                skipped.append([s.name, _classify_dir(s.name)])
                continue
            s_num = f"{_prefix_of(s.name):02d}"
            subs[s_num] = {"name": s.name}
            # Rule 4: L3+ is out of scope — record but never add.
            for l3 in s.iterdir():
                if l3.is_dir():
                    l3_excluded.append(str(l3.relative_to(root)))

    # Diff against the previous tree for the report.
    for k in tree:
        if k not in old:
            added.append(f"L1 {tree[k]['name']}")
        elif old[k].get("name") != tree[k]["name"]:
            updated.append(f"L1 {tree[k]['name']}")
        for sk in tree[k].get("sub", {}):
            if sk not in old.get(k, {}).get("sub", {}):
                added.append(f"L2 {k}/{tree[k]['sub'][sk]['name']}")
            elif old[k]["sub"][sk].get("name") != tree[k]["sub"][sk]["name"]:
                updated.append(f"L2 {k}/{tree[k]['sub'][sk]['name']}")
    removed = _tree_diff_removed(old, tree)

    if apply and (added or updated or removed):
        _write_workspace_tree(tree)

    return {
        "root": str(root),
        "added": added,
        "updated": updated,
        "removed": removed,
        "skipped": skipped,
        "l3_excluded": l3_excluded,
        "applied": bool(apply and (added or updated or removed)),
    }


def _tree_diff_removed(old: dict, new: dict) -> list[str]:
    """Entries present in *old* but absent from *new* (removed by the mirror)."""
    removed: list[str] = []
    for k, v in old.items():
        if k not in new:
            removed.append(f"L1 {v.get('name', k)}")
            continue
        for sk, sv in v.get("sub", {}).items():
            if sk not in new.get(k, {}).get("sub", {}):
                removed.append(f"L2 {k}/{sv.get('name', sk)}")
    return removed


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


def _cmd_scan() -> None:
    apply = "--apply" in sys.argv[2:]
    print(json.dumps(scan_workspace(apply=apply), ensure_ascii=False))


def main() -> None:
    cmds = {
        "generate": _cmd_generate,
        "bump":     _cmd_bump,
        "archive":  _cmd_archive,
        "tree":     _cmd_tree,
        "root":     _cmd_root,
        "upsert":   _cmd_upsert,
        "scan":     _cmd_scan,
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
