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

Global context flags (accepted by any command; passed by the calling AI):
    --author <name>          the real author the AI identified
    --root <path>            explicit workspace root; adopted AND persisted to
                             config.local.json when config has no root
    --context-root <path>    session-inferred root; used only when config is
                             empty and no --root was given — NEVER persisted

Commands:
    generate  <title> <ext> [--type <type>] [--author <author>]
              [--date YYYYMMDD] [--suffix final|refer] [--l2 <subtype>]
                                           # resolve type (3-tier: config match
                                           # > AI define > language default),
                                           # auto-upsert the L1 (and optional
                                           # L2) into config + disk, return
                                           # save_path/l1/l2
    bump      <filename> <major|minor|patch>
    archive   <file_path>
    tree                                   # print directory_tree (runs the
                                           # per-invocation additive sync first)
    root                                   # resolve workspace root (4-tier:
                                           # config > --root > --context-root >
                                           # default DocumentSpace)
    upsert    --l1 <type> [--l2 <type>]    # ensure L1/L2 exists (01-numbering),
                                           # write back to config.local.json
    scan      [--apply]                    # full mirror of L1/L2 dirs on disk
                                           # into the tree (rules 1-4;
                                           # add/update/remove); --apply writes
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
_OTHER_ALIASES = {"other", "others", "其它", "其它"}  # aliases that map to the 99 entry

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
    global _tree_cache
    _tree_cache = None
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


def _ensure_dirs_on_disk(tree: dict) -> None:
    """Create any L1/L2 directories declared in *tree* but missing on disk.

    Used after bootstrapping an empty config tree from a baseline, so the
    on-disk structure is materialized and subsequent runs read from config
    (no re-creation needed). This only creates missing dirs; it never prunes.
    """
    root = Path(_resolve_workspace_root()["root"])
    for l1k, l1v in tree.items():
        l1p = root / str(l1v.get("name", l1k))
        l1p.mkdir(parents=True, exist_ok=True)
        for l2k, l2v in (l1v.get("sub") or {}).items():
            (l1p / str(l2v.get("name", l2k))).mkdir(parents=True, exist_ok=True)


def _sync_tree_additive() -> None:
    """Additively sync the on-disk root into the config tree (add-only).

    Runs on each skill invocation when the resolved root is "configured"
    (source != "default"). For every numbered content L1/L2 directory present
    on disk but missing from the config tree, add it (preserving its number).
    Entries present in config but absent on disk are NEVER removed — config is
    the category source of truth; deletions are not auto-pruned.

    Realises requirement 4: keep config in sync with disk *additions* only.
    """
    info = _resolve_workspace_root()
    if info["source"] == "default":
        return  # no configured root -> do not check
    root = Path(info["root"])
    if not root.exists():
        return
    tree = _parse_workspace_tree()
    changed = False
    for d in sorted(root.iterdir()):
        if not d.is_dir() or _classify_dir(d.name) != "content":
            continue
        l1_num = f"{_prefix_of(d.name):02d}"
        if l1_num not in tree:
            tree[l1_num] = {"name": d.name, "type": _core_name(d.name), "sub": {}}
            changed = True
        subs = tree[l1_num].setdefault("sub", {})
        for s in sorted(d.iterdir()):
            if not s.is_dir() or _classify_dir(s.name) != "content":
                continue
            s_num = f"{_prefix_of(s.name):02d}"
            if s_num not in subs:
                subs[s_num] = {"name": s.name}
                changed = True
    if changed:
        _write_workspace_tree(tree)


def _ensure_tree() -> dict:
    """Return the merged directory tree (config.local.json over config.json).

    On each call, an additive disk->config sync runs first (see
    `_sync_tree_additive`) so the tree tracks new on-disk directories without
    ever deleting config entries. Result is cached for the process lifetime and
    invalidated by any tree write.
    """
    global _tree_cache
    if _tree_cache is not None:
        return _tree_cache
    _sync_tree_additive()
    _tree_cache = _parse_workspace_tree()
    return _tree_cache


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
        "default_author": str(raw.get("default_author") or "").strip(),
        "default_extension": (str(raw.get("default_extension") or "md").strip().lstrip(".").lower() or "md"),
        "allowed_extensions": allowed or list(_DEFAULT_ALLOWED),
        "workspace_root": str(raw.get("workspace_root") or "").strip(),
        "directory_tree": _parse_workspace_tree(),
    }


_config = _load_config()

# AI-context layers (passed by the calling AI from its session):
#   _CTX_AUTHOR        — the real author the AI identified (--author)
#   _CTX_ROOT          — an explicitly provided root (--root / --workspace-root);
#                         when config has no root, this is adopted AND persisted
#                         into config.local.json (becomes the future config)
#   _CTX_INFERRED_ROOT — a root the AI inferred from session context
#                         (--context-root); used only when config has no root and
#                         none was explicitly provided — NEVER persisted
# Static config always wins over any of these (config > provided > context > default).
_CTX_AUTHOR = ""
_CTX_ROOT = ""
_CTX_INFERRED_ROOT = ""
_tree_cache = None  # lazy directory tree (additively synced from disk per call)


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
#  Workspace root resolution — 4-tier: config → explicit --root (persisted) →
#  --context-root (session-inferred, not persisted) → default DocumentSpace
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


def _persist_workspace_root(path: str) -> bool:
    """Persist the workspace root into config.local.json (machine-local).

    Used only when the config had no root and one was explicitly provided
    (tier 2). Preserves every other local key (e.g. directory_tree). Writes
    never touch config.json (the shared baseline). Returns True on success.
    """
    local = _read_json(_config_local_path())
    local["workspace_root"] = path
    try:
        _config_local_path().write_text(
            json.dumps(local, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def _resolve_workspace_root() -> dict:
    """Resolve the absolute workspace root through the 4-tier chain:

      1. config — `workspace_root` from the merged config (config.local.json
                  overrides config.json) — authoritative when non-empty
      2. explicit — `--root` / `--workspace-root` passed by the AI from an
                  explicit user/AI instruction; when config has no root, this is
                  adopted AND persisted into config.local.json (source="root")
      3. context — `--context-root` the AI inferred from its session context
                  (e.g. the project/session directory); used when config has no
                  root and none was explicitly provided — NEVER persisted
                  (source="context")
      4. default — `<system user root>/DocumentSpace` (created if missing)

    Returns {"root": <abs path>, "source": "config|root|context|default",
             "created": bool}. Tiers 2-4 create the directory when missing.

    NOTE: a user-specified root is LOWER priority than an existing config root —
    it only takes effect (and persists) when the config root is empty. "User
    highest priority" applies to the L1/L2 save-directory choice, not to
    overriding an already-configured root.
    """
    cfg = _configured_workspace_root()
    if cfg:
        return {"root": str(Path(cfg)), "source": "config", "created": False}

    if _CTX_ROOT and _CTX_ROOT.strip():
        p = Path(_CTX_ROOT.strip())
        created = not p.exists()
        p.mkdir(parents=True, exist_ok=True)
        _persist_workspace_root(str(p))
        return {"root": str(p), "source": "root", "created": created}

    if _CTX_INFERRED_ROOT and _CTX_INFERRED_ROOT.strip():
        p = Path(_CTX_INFERRED_ROOT.strip())
        created = not p.exists()
        p.mkdir(parents=True, exist_ok=True)
        return {"root": str(p), "source": "context", "created": created}

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
    """Resolve author: config default_author → AI context → 'Unknown'.

    Priority (config is authoritative; AI context only fills the gap):
      1) config default_author
      2) the author the AI identified from its session (--author / context_author)
      3) hardcoded 'Unknown' fallback
    """
    cfg = _cfg("default_author", "").strip()
    if cfg:
        return cfg
    ctx = (context_author or _CTX_AUTHOR or "").strip()
    if ctx:
        return ctx
    return "Unknown"


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
    tree = _ensure_tree()
    created = False
    root = Path(_resolve_workspace_root()["root"])

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
        (root / tree[l1_key]["name"]).mkdir(parents=True, exist_ok=True)

    result = {
        "l1": l1_key,
        "l1_name": tree[l1_key]["name"],
        "l2": None,
        "l2_name": None,
        "created": created,
    }

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
            (root / tree[l1_key]["name"] / subs[l2_key]["name"]).mkdir(
                parents=True, exist_ok=True
            )
        result["l2"] = l2_key
        result["l2_name"] = subs[l2_key]["name"]

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
             "--type <type> --author <author> [--date YYYYMMDD] "
             "[--suffix final|refer] [--l2 <subtype>]")

    _ensure_tree()  # additive disk->config sync (config -> disk additions)
    opts = _parse_flags(sys.argv[4:], {
        "--type":   "file_type",
        "--author": "author",
        "--date":   "date_str",
        "--suffix": "suffix",
        "--l2":     "l2",
    })

    title = sys.argv[2]
    ext = sys.argv[3]
    lang = _doc_lang(title)
    raw_type = (opts.get("file_type") or "").strip()

    # Type resolution (3-tier): AI passes the config-matched type; if empty or an
    # explicit "other" alias, fall back to the language-adapted default
    # ("其它" for Chinese, "Other" for English) which reuses the 99 entry.
    if raw_type and raw_type.lower() in _OTHER_ALIASES:
        directory_type = _FALLBACK_TYPE
        prefix = "其它" if lang == "zh" else "Other"
    elif raw_type:
        directory_type = raw_type
        prefix = raw_type
    else:
        directory_type = _FALLBACK_TYPE
        prefix = "其它" if lang == "zh" else "Other"

    # Auto-complete the directory tree: ensure the L1 (and optional L2) exists
    # on disk and in config (persisted). New dirs are created here.
    ups = upsert_dir(directory_type, opts.get("l2", ""))
    root = Path(_resolve_workspace_root()["root"])
    save_path = root / ups["l1_name"]
    if ups["l2_name"]:
        save_path = save_path / ups["l2_name"]

    try:
        result = generate_name(
            title, ext, prefix,
            opts.get("author", ""),
            opts.get("date_str", ""),
            opts.get("suffix", ""),
        )
    except ValueError as e:
        _err(str(e))

    result["save_path"] = str(save_path)
    result["l1"] = ups["l1"]
    result["l2"] = ups["l2"]
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
    print(json.dumps(_ensure_tree(), ensure_ascii=False, indent=2))


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
    global _CTX_AUTHOR, _CTX_ROOT, _CTX_INFERRED_ROOT
    # AI-context flags (config > explicit --root > inferred --context-root >
    # fallback). Parsed globally so any command can carry the caller's context.
    # A user/AI-explicit --root persists into config when config has no root;
    # --context-root is session-inferred and never persisted.
    for i, a in enumerate(sys.argv):
        if a == "--author" and i + 1 < len(sys.argv):
            _CTX_AUTHOR = sys.argv[i + 1]
        elif a in ("--root", "--workspace-root") and i + 1 < len(sys.argv):
            _CTX_ROOT = sys.argv[i + 1]
        elif a in ("--context-root", "--context-workspace-root") and i + 1 < len(sys.argv):
            _CTX_INFERRED_ROOT = sys.argv[i + 1]

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
