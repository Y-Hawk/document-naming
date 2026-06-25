#!/usr/bin/env python3
"""Document naming tool — generate, bump, and archive compliant filenames.

Format: see references/rules.md

Commands:
    generate  <title> <ext> --type <type> --author <author>
              [--date YYYYMMDD] [--suffix final|refer]
    bump      <filename> <major|minor|patch>
    archive   <file_path>

Stdlib only — no external dependencies.
"""

import json, re, sys
from datetime import date
from pathlib import Path


# =============================================================================
#  Configuration
# =============================================================================

def _skill_root() -> Path:
    """Resolve skill root directory (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent

_SKILL_ROOT = _skill_root()

# Scalar keys in workspace dict — flattened to top level
_WS_KEYS = {"workspace_root", "archive_dir_name", "refer_dir_name", "fallback_dir_name"}
# Note: directory_tree is also extracted from workspace dict/file but handled separately
# (it's a nested structure, not a scalar value). See _load_config() for details.


def _read_json(path: Path) -> dict:
    """Read a JSON file; return empty dict on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _parse_workspace_file(cfg: dict) -> dict:
    """Parse workspace config file and return extracted data dict.

    Returns dict with scalar keys and directory_tree.
    Returns empty dict if file not found, path empty, or parse fails.
    """
    ws_config_path = cfg.get("workspace_config_path", "")
    if not ws_config_path:
        return {}

    ws_path = Path(ws_config_path)
    if not ws_path.is_absolute():
        ws_path = _SKILL_ROOT / ws_config_path

    try:
        text = ws_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    result = {}

    # ── Configuration section (scalar keys) ──
    section = re.search(
        r"^## Configuration\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if section:
        for m in re.finditer(r"\|\s*`(\w+)`\s*\|\s*`([^`]+)`\s*\|", section.group(1)):
            key, raw_value = m.group(1), m.group(2).strip('"')
            if key in _WS_KEYS:
                result[key] = raw_value

    # ── Build directory_tree from Directory→Type + Sub-directory ──
    dir_section = re.search(
        r"^## Directory→Type Mapping\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    sub_section = re.search(
        r"^## Sub-directory Structure\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )

    tree = {}
    if dir_section:
        for m in re.finditer(r"\|\s*`([^`]+)`\s*\|\s*`(\w+)`\s*\|", dir_section.group(1)):
            dir_name = m.group(1).rstrip("/")
            tree[dir_name] = {"name": dir_name, "type": m.group(2), "sub": {}}

    if sub_section:
        for m in re.finditer(r"\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", sub_section.group(1)):
            parent = m.group(1).rstrip("/")
            subdir = m.group(2).rstrip("/")
            if parent in tree:
                tree[parent]["sub"][subdir] = {"name": subdir}

    if tree:
        result["directory_tree"] = tree

    return result


def _load_config() -> dict:
    """Load config.local.json → config.json → flatten workspace dict → workspace file (if enabled).

    Merge order: config.local.json overrides config.json;
    workspace dict flattened to top level (non-empty values);
    workspace config file supplements when enable_workspace_path is true.
    Priority: workspace file → config dict → hard-coded defaults.
    When workspace file unavailable, fall back to config dict values.
    """
    cfg = _read_json(_SKILL_ROOT / "config.json")
    if not cfg:
        return cfg

    local = _read_json(_SKILL_ROOT / "config.local.json")
    if local:
        cfg.update(local)

    # Flatten workspace sub-dict into top level
    ws = cfg.pop("workspace", {})

    # Parse workspace file when switch is on (enable_workspace_path is top-level key)
    ws_file_data = {}
    if cfg.get("enable_workspace_path", True):
        ws_file_data = _parse_workspace_file(cfg)

    # Priority: workspace file → config dict → defaults
    # When file readable: file values take priority; dict fills gaps.
    # When file not readable: dict values are the only source.
    for key in _WS_KEYS:
        val = ws_file_data.get(key, "")      # Try file first
        if not val:
            val = ws.get(key, "")             # Fall back to config dict
        if val:
            cfg[key] = val

    # directory_tree: same priority (file → dict)
    tree = ws_file_data.get("directory_tree")
    if not tree:
        tree = ws.get("directory_tree")
    if tree:
        cfg["directory_tree"] = tree

    return cfg


_config = _load_config()


def _cfg(key: str, default: str = "") -> str:
    """Read a merged config value, returning *default* if key is absent."""
    return str(_config.get(key, default))


def _allowed_extensions() -> list[str]:
    """Return the allowed_extensions whitelist from merged config.

    Fallback: ["md", "pptx", "xlsx", "docx", "pdf", "png", "mp4", "mp3"].
    All items are lowercase, no leading dots.
    """
    exts = _config.get("allowed_extensions")
    if isinstance(exts, list) and exts:
        return [e.lower().lstrip(".") for e in exts if isinstance(e, str)]
    return ["md", "pptx", "xlsx", "docx", "pdf", "png", "mp4", "mp3"]


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

    prefix = file_type.strip() or _cfg("fallback_dir_name", "other")
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

    # Reconstruct from parts — avoids string-replace hitting the wrong field
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

    print(json.dumps(
        generate_name(
            sys.argv[2], sys.argv[3],
            opts.get("file_type", ""),
            opts.get("author", ""),
            opts.get("date_str", ""),
            opts.get("suffix", ""),
        ),
        ensure_ascii=False,
    ))


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


def main() -> None:
    cmds = {"generate": _cmd_generate, "bump": _cmd_bump, "archive": _cmd_archive}

    if len(sys.argv) < 2:
        _err(f"Usage: naming.py <{'|'.join(cmds)}> [args...]")

    cmd = sys.argv[1]
    if cmd in cmds:
        cmds[cmd]()
    else:
        _err(f"Unknown command: '{cmd}'")


if __name__ == "__main__":
    main()
