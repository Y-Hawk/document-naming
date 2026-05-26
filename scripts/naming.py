#!/usr/bin/env python3
"""
Document naming tool — generate, bump, and archive compliant filenames.

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
#  Configuration loading
# =============================================================================
# Config is loaded once at import time from two sources:
#   1. config.json (skill-level defaults)
#   2. workspace config Configuration table (workspace-level overrides)
#
# workspace_root resolution: caller-specified → Desktop → context/system-matched directory


def _load_config() -> dict:
    """Load and merge config.json + workspace config Configuration.

    Returns merged dict, or empty dict if both sources are unreadable.
    Never raises — all errors are silently swallowed.
    """
    # ---- Load config.json ----
    candidates = [
        Path(__file__).resolve().parent.parent / "config.json",
        Path.cwd() / "config.json",
    ]
    cfg = {}
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                break
            except (json.JSONDecodeError, OSError):
                pass

    if not cfg:
        return cfg

    # ---- Merge workspace config Configuration section ----
    _merge_workspace_config(cfg)

    # ---- workspace_root: caller-specified → Desktop → context/system ----
    # _load_config only merges what's available; runtime priority is evaluated by caller

    return cfg


def _merge_workspace_config(cfg: dict) -> None:
    """Parse workspace config ``## Configuration`` table and merge into *cfg*.

    Reads the table rows and extracts config keys not already present in cfg.
    Supported keys: workspace_root, archive_dir_name, refer_dir_name, fallback_dir_name.
    """
    ws_config_path = cfg.get("workspace_config_path", "")
    if not ws_config_path:
        return

    skill_root = Path(__file__).resolve().parent.parent
    ws_path = skill_root / ws_config_path
    if not ws_path.exists():
        return

    try:
        with open(ws_path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return

    # Locate ## Configuration section and extract key→value from markdown table.
    # Table row format: | `key_name` | description | `"default"` |
    section = re.search(
        r"^## Configuration\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if not section:
        return

    ws_values = {
        m.group(1): m.group(2).strip('"')
        for m in re.finditer(
            r"\| `(\w+)` \| .*? \| ``?\"([^\"]+)\"``? \|", section.group(1)
        )
    }

    # Only set keys not already present from config.json
    for k in ("workspace_root", "archive_dir_name", "refer_dir_name", "fallback_dir_name"):
        if k not in cfg and k in ws_values:
            cfg[k] = ws_values[k]


_config = _load_config()


def _cfg(key: str, default: str = "") -> str:
    """Read a merged config value, returning *default* if key is absent."""
    return str(_config.get(key, default))


# =============================================================================
#  Filename regex — canonical format
# =============================================================================
# Groups:
#   $1  type       leading segment before first underscore
#   $2  title      free-form, sanitised before construction
#   $3  date       8-digit YYYYMMDD
#   $4  version    semantic version X.Y.Z (no leading v)
#   $5  suffix     optional .final or .refer (including leading dot), or None
#   $6  author     word characters only
#   $7  extension  file suffix after final dot

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
    """Resolve author: caller context → config.json default_author → 'Unknown'."""
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
        "suffix":  m.group(5) or "",       # ".final" / ".refer" / ""
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

    Args:
        title:     Document title (sanitised to ≤30 chars, filesystem-safe).
        ext:       File extension (leading dot stripped).
        file_type: Type prefix from Step 1 resolution.
        author:    Author name from caller context.
        date_str:  Override date as YYYYMMDD (default: today).
        suffix:    'final' or 'refer' to append to version (default: none).

    Returns: {"name", "type", "title", "date", "version", "suffix", "author", "ext"}
    """
    # Type — caller provides resolved type; fallback to fallback_dir_name
    prefix = file_type.strip() or _cfg("fallback_dir_name", "other")

    # Title — sanitised
    t = _sanitize(title)

    # Date — override or today
    d = date_str or date.today().strftime("%Y%m%d")

    # Author — three-tier chain
    a = _resolve_author(author)

    # Version — always v1.0.0 for new docs
    v = "v1.0.0"

    # Suffix — append .final or .refer if caller specifies
    s = ""
    if suffix in ("final", "refer"):
        s = f".{suffix}"
        v += s

    # Extension — strip leading dot
    e = ext.lstrip(".")

    # Assemble
    name = f"{prefix}_{t}_{d}_{v}_{a}.{e}"
    return {
        "name":    name,
        "type":    prefix,
        "title":   t,
        "date":    d,
        "version": v,
        "suffix":  s,
        "author":  a,
        "ext":     e,
    }


def bump_version(filename: str, level: str = "patch") -> dict:
    """Bump version number and refresh date to today.

    Increments version per semver semantics. Preserves existing .final/.refer
    suffix from the original filename.

    Args:
        filename: Existing compliant filename.
        level:    'major' | 'minor' | 'patch'.

    Raises ValueError if filename is not compliant.

    Returns: {"old_name", "new_name", "old_version", "new_version"}
    """
    p = parse_filename(filename)
    if not p:
        raise ValueError(f"Non-compliant filename: {filename}")

    # ---- Semantic version increment ----
    major, minor, patch = map(int, p["version"].split("."))
    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    else:
        # Default 'patch' — also catches unrecognised levels
        patch += 1

    new_ver = f"v{major}.{minor}.{patch}"
    new_ver_with_suffix = new_ver + p["suffix"]

    # ---- Refresh date to today ----
    today = date.today().strftime("%Y%m%d")

    # ---- Reconstruct — replace version then date ----
    old_ver_full = f"v{p['version']}{p['suffix']}"
    new = (
        filename
        .replace(old_ver_full, new_ver_with_suffix, 1)
        .replace(p["date"], today, 1)
    )

    return {
        "old_name":    filename,
        "new_name":    new,
        "old_version": old_ver_full,
        "new_version": new_ver_with_suffix,
    }


def archive_old_version(file_path: str | Path) -> Path | None:
    """Move a file into the appropriate archive sub-directory.

    Routing by version suffix:
      (none)  → <source_parent>/<archive_dir_name>/
      .refer  → <source_parent>/<refer_dir_name>/
      .final  → NOT moved (returns None without error)

    Target directory is created if missing. Name collisions are resolved
    by appending _1, _2, ... before the extension.

    Returns destination Path on success, or None if:
      - source file does not exist
      - suffix is .final (no move needed)
    """
    src = Path(file_path)

    # Guard: source must exist
    if not src.exists():
        return None

    # Parse suffix from filename to determine target directory
    parsed = parse_filename(src.name)

    # .final files are NOT moved
    if parsed and parsed.get("suffix") == ".final":
        return None

    # Determine target sub-directory name
    if parsed and parsed.get("suffix") == ".refer":
        dir_name = _cfg("refer_dir_name", "refer")
    else:
        dir_name = _cfg("archive_dir_name", "history")

    archive_dir = src.parent / dir_name
    archive_dir.mkdir(exist_ok=True)

    # Resolve collisions
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


def _cmd_generate() -> None:
    """CLI: naming.py generate <title> <ext> --type <type> --author <author>
           [--date YYYYMMDD] [--suffix final|refer]"""
    if len(sys.argv) < 4:
        _err("Usage: naming.py generate <title> <ext> "
             "--type <type> --author <author> [--date YYYYMMDD] [--suffix final|refer]")

    title  = sys.argv[2]
    ext    = sys.argv[3]

    file_type = ""
    author    = ""
    date_str  = ""
    suffix    = ""

    i = 4
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--type"   and i + 1 < len(sys.argv):
            file_type = sys.argv[i + 1]; i += 1
        elif a == "--author" and i + 1 < len(sys.argv):
            author    = sys.argv[i + 1]; i += 1
        elif a == "--date"   and i + 1 < len(sys.argv):
            date_str  = sys.argv[i + 1]; i += 1
        elif a == "--suffix" and i + 1 < len(sys.argv):
            suffix    = sys.argv[i + 1]; i += 1
        # Unrecognised flags are silently skipped
        i += 1

    print(json.dumps(
        generate_name(title, ext, file_type, author, date_str, suffix),
        ensure_ascii=False,
    ))


def _cmd_bump() -> None:
    """CLI: naming.py bump <filename> <major|minor|patch>"""
    if len(sys.argv) < 4:
        _err("Usage: naming.py bump <filename> <major|minor|patch>")

    filename = sys.argv[2]
    level    = sys.argv[3]

    if level not in ("major", "minor", "patch"):
        _err(f"Invalid bump level: '{level}'. Use major/minor/patch.")

    try:
        print(json.dumps(bump_version(filename, level), ensure_ascii=False))
    except ValueError as e:
        _err(str(e))


def _cmd_archive() -> None:
    """CLI: naming.py archive <file_path>"""
    if len(sys.argv) < 3:
        _err("Usage: naming.py archive <file_path>")

    src = Path(sys.argv[2])

    if not src.exists():
        _err(f"File not found: {src}")

    dest = archive_old_version(src)
    if dest:
        print(json.dumps(
            {"archived": str(src), "to": str(dest)},
            ensure_ascii=False,
        ))
    else:
        # Source is .final or archive failed silently
        print(json.dumps(
            {"archived": str(src), "to": None, "note": "file is .final — not moved"},
            ensure_ascii=False,
        ))


def main() -> None:
    """Dispatch to sub-command."""
    cmds = {
        "generate": _cmd_generate,
        "bump":     _cmd_bump,
        "archive":  _cmd_archive,
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
