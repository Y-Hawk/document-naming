#!/usr/bin/env python3
"""
Document naming tool — generate, bump, and archive compliant filenames.
Format: Type_Title_YYYYMMDD_v1.0.0_Author.ext

Commands:
    generate  <title> <ext> --type <type> --author <author> [--date YYYYMMDD]
    bump      <filename> <major|minor|patch>
    archive   <file_path>

Stdlib only — no external dependencies (json, re, sys, datetime, pathlib).
"""

import json, re, sys
from datetime import date
from pathlib import Path

# =============================================================================
#  Configuration loading
# =============================================================================
# All tunable defaults live in config.json (at the skill root, one level above
# this script).  The script loads config.json at import time as a secondary
# fallback — the AI caller resolves values first, and only passes them to the
# script when needed.  If config.json is missing or unreadable, all _cfg()
# calls return their hardcoded default argument.

def _load_config() -> dict:
    """Load config.json from two candidate locations.

    Candidates (tried in order):
      1. <skill_root>/config.json  —  sibling of the scripts/ directory.
      2. $CWD/config.json          —  current working directory fallback.

    Returns an empty dict if no file is found or if JSON is malformed.
    """
    candidates = [
        Path(__file__).resolve().parent.parent / "config.json",
        Path.cwd() / "config.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                # Silently skip corrupted / unreadable files — the hardcoded
                # defaults in each _cfg() call are the ultimate fallback.
                pass
    return {}

# Load once at import time — cheap, and config rarely changes during a session.
_config = _load_config()

def _cfg(key: str, default: str = "") -> str:
    """Read a config value, returning *default* if the key is absent.

    Always returns a string.  The per-call default is the hardcoded
    ultimate fallback when config.json is missing the key entirely.
    """
    return str(_config.get(key, default))


# =============================================================================
#  Filename regex
# =============================================================================
# Matches the canonical format: Type_Title_YYYYMMDD_vX.Y.Z_Author.ext
#
# Capture groups:
#   $1  type      — leading segment before the first underscore (e.g. "guide")
#                   Any non-underscore characters.  AI-resolved, no enum.
#   $2  title     — free-form text between type and date.  Spaces collapsed,
#                   illegal chars stripped by _sanitize() before construction.
#   $3  date      — 8-digit YYYYMMDD.  Today by default; refreshed on bump.
#   $4  version   — semantic version vX.Y.Z (all digits).  Always v1.0.0 for
#                   new docs; bumped on edit.
#   $5  author    — word characters only (no dots / hyphens).  Resolved from
#                   context → config → "Unknown".
#   $6  extension — file suffix after the final dot (e.g. "md", "html").
#
# Used by parse_filename (for reading) and as the spec that all generation
# functions must conform to.

FILENAME_RE = re.compile(
    r"^([^_]+)_(.+)_(\d{8})_v(\d+\.\d+\.\d+)_(\w+)\.(\w+)$"
)


# =============================================================================
#  Internal helpers
# =============================================================================

def _sanitize(title: str) -> str:
    """Sanitise a title for use as a filename segment.

    Pipeline:
      1. Strip characters illegal on Windows: \\ / : * ? " < > |
      2. Trim leading and trailing whitespace.
      3. Collapse internal spaces (concatenate words directly).
      4. Truncate to 30 characters max.
      5. If the result is empty, return "untitled".

    Returns a clean, ≤30-char, filesystem-safe title string.
    """
    clean = re.sub(r'[\\/:*?"<>|]', "", title).strip().replace(" ", "")
    return clean[:30] or "untitled"


def _resolve_author(context_author: str = "") -> str:
    """Resolve the author name through a three-tier fallback chain.

    Chain:
      1. context_author  —  from SOUL.md / IDENTITY.md, passed by AI caller.
      2. config.json → default_author  —  "Kai" by default.
      3. "Unknown"  —  hardcoded last resort.

    Returns a non-empty author string in all cases.
    """
    if context_author and context_author.strip():
        return context_author.strip()
    fb = _cfg("default_author", "Kai")
    return fb.strip() or "Unknown"


# =============================================================================
#  Core API  (callable from Python as well as CLI)
# =============================================================================

def parse_filename(filename: str) -> dict | None:
    """Parse a compliant filename into its structured fields.

    Returns a dict with keys: type, title, date, version, author, ext.
    Returns None if the filename does not match the canonical format.
    Does not validate field semantics — only structural conformance.
    """
    m = FILENAME_RE.match(filename)
    if not m:
        return None
    return {
        "type":    m.group(1),
        "title":   m.group(2),
        "date":    m.group(3),
        "version": m.group(4),
        "author":  m.group(5),
        "ext":     m.group(6),
    }


def generate_name(title: str, ext: str, file_type: str = "",
                  author: str = "", date_str: str = "") -> dict:
    """Generate a compliant filename for a **new** document.  No disk I/O.

    Each field is resolved independently, assembled, and returned as both
    a flat "name" and individual keys for downstream use (mv / Write).

    Field resolution order (mirrors SKILL.md Step 2 field-resolution chains):
      type    — file_type arg  →  config default_type ("other")
      title   — _sanitize(title)  →  "untitled"
      date    — date_str arg (YYYYMMDD)  →  today
      version — always "v1.0.0" (hardcoded, no override)
      author  — _resolve_author(author)
      ext     — ext arg (leading dot stripped)  →  config default_extension ("md")

    Returns: {"name", "type", "title", "date", "version", "author", "ext"}
    """
    # Type: AI-caller provides the resolved type from Step 1; fallback to
    # config.json → default_type ("other").
    prefix = file_type.strip() or _cfg("default_type", "other")

    # Title: sanitised to ≤30 chars, filesystem-safe.
    t = _sanitize(title)

    # Date: explicit override (e.g. back-dated) or today.
    d = date_str or date.today().strftime("%Y%m%d")

    # Author: three-tier chain (context → config → "Unknown").
    a = _resolve_author(author)

    # Version: always v1.0.0 for new documents — no override.
    v = "v1.0.0"

    # Extension: strip any leading dot the caller might have included.
    e = ext.lstrip(".")

    # Assemble: underscore-separated, extension after final dot.
    name = f"{prefix}_{t}_{d}_{v}_{a}.{e}"
    return {
        "name":    name,
        "type":    prefix,
        "title":   t,
        "date":    d,
        "version": v,
        "author":  a,
        "ext":     e,
    }


def bump_version(filename: str, level: str = "patch") -> dict:
    """Bump the version number and refresh the date to today.

    Used for the **edit** scenario.  Parses the existing compliant filename,
    increments the version according to semver semantics, and replaces the
    date substring with today's date.  Title, type, author, and extension
    are preserved unchanged.

    Bump levels (matches SKILL.md bump level semantics table):
      major  —  X+1.0.0    (full restructure)
      minor  —  X.Y+1.0    (content changes)
      patch  —  X.Y.Z+1    (format / typo fixes)

    The replacement strategy is string-based (not reconstruction from parts)
    to minimise the chance of accidentally altering the title or author:
      - version substring (e.g. "v1.0.0") → replaced at its first occurrence.
      - date substring (e.g. "20260520")  → replaced at its first occurrence.

    Raises ValueError if the filename is not compliant.
    Returns: {"old_name", "new_name", "old_version", "new_version"}
    """
    p = parse_filename(filename)
    if not p:
        raise ValueError(f"Non-compliant filename: {filename}")

    # ── Semantic versioning increment ──────────────────────────────────
    major, minor, patch = map(int, p["version"].split("."))
    if level == "major":
        major += 1; minor = 0; patch = 0
    elif level == "minor":
        minor += 1; patch = 0
    else:
        # Default "patch" — also catches any unrecognised level that made
        # it past CLI validation.
        patch += 1

    new_ver = f"v{major}.{minor}.{patch}"

    # ── Refresh date to today ──────────────────────────────────────────
    today = date.today().strftime("%Y%m%d")

    # ── Reconstruct: replace version (first occurrence), then date ─────
    # Using str.replace with count=1 avoids touching a version-like
    # substring that might appear in the title (unlikely but safe).
    new = (
        filename
        .replace(f"v{p['version']}", new_ver, 1)
        .replace(p["date"], today, 1)
    )

    return {
        "old_name":    filename,
        "new_name":    new,
        "old_version": f"v{p['version']}",
        "new_version": new_ver,
    }


def archive_old_version(file_path: str | Path) -> Path | None:
    """Move a file into the archive sub-directory.

    Used for the **edit** scenario after bump_version has produced a new
    filename.  The old file is moved (not copied) into <parent>/<archive>/
    where <archive> comes from config.json → archive_dir_name ("history"
    by default).

    Collision handling:
      If a file with the same name already exists in the archive directory,
      numeric suffixes are appended: filename_1.ext, filename_2.ext, ...
      The loop increments until a unique name is found.

    The archive directory is created if it does not already exist.

    Returns the destination Path on success, or None if the source file
    does not exist.
    """
    src = Path(file_path)

    # ── Guard: source must exist ───────────────────────────────────────
    if not src.exists():
        return None

    # ── Prepare archive directory ──────────────────────────────────────
    archive_dir_name = _cfg("archive_dir_name", "history")
    archive_dir = src.parent / archive_dir_name
    archive_dir.mkdir(exist_ok=True)

    # ── Determine destination; avoid overwrites ────────────────────────
    dest = archive_dir / src.name
    if dest.exists():
        n = 1
        while dest.exists():
            # Append _1, _2, ... before the extension.
            dest = archive_dir / f"{src.stem}_{n}{src.suffix}"
            n += 1

    # ── Move (rename) into archive ─────────────────────────────────────
    src.rename(dest)
    return dest


# =============================================================================
#  CLI  (thin wrappers over the Core API)
# =============================================================================
# Each sub-command does four things:
#   1. Validate argument count → print JSON error + exit(1) if insufficient.
#   2. Parse arguments from sys.argv.
#   3. Call the corresponding Core API function.
#   4. Print the result as JSON to stdout.
#
# All output (success and error) is JSON — the AI caller parses it uniformly.

def _err(msg: str, code: int = 1) -> None:
    """Print a JSON error object and exit with the given code.

    Uniform error format: {"error": "<message>"}
    All CLI commands use this to guarantee consistent output shape.
    """
    print(json.dumps({"error": msg}))
    sys.exit(code)


def _cmd_generate() -> None:
    """CLI handler: ``naming.py generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD]``.

    Positional args: <title> (str), <ext> (str) — required.
    Optional flags:  --type, --author, --date — each followed by its value.
                     Flags may appear in any order; unrecognised flags are
                     silently ignored (not an error — allows future extension).

    Calls generate_name() and prints the result as JSON.
    """
    # Need at least: argv[0]=script, [1]=generate, [2]=title, [3]=ext
    if len(sys.argv) < 4:
        _err("Usage: naming.py generate <title> <ext> "
             "--type <type> --author <author> [--date YYYYMMDD]")

    # Positional arguments — always at indices 2 and 3.
    title = sys.argv[2]
    ext   = sys.argv[3]

    # Optional flags — default to empty string (let generate_name apply fallbacks).
    file_type = ""
    author    = ""
    date_str  = ""

    # Manual flag parsing — starts at argv[4].  Each recognised flag consumes
    # the next argv entry as its value (i += 1 skips the value on next iteration).
    i = 4
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--type"     and i + 1 < len(sys.argv):
            file_type = sys.argv[i + 1]; i += 1
        elif a == "--author" and i + 1 < len(sys.argv):
            author    = sys.argv[i + 1]; i += 1
        elif a == "--date"   and i + 1 < len(sys.argv):
            date_str  = sys.argv[i + 1]; i += 1
        # else: unrecognised flag → silently skip (not an error).
        i += 1

    # Generate and print — ensure_ascii=False keeps non-ASCII titles readable.
    print(json.dumps(
        generate_name(title, ext, file_type, author, date_str),
        ensure_ascii=False,
    ))


def _cmd_bump() -> None:
    """CLI handler: ``naming.py bump <filename> <major|minor|patch>``.

    Pre-validates the bump level before calling bump_version.  Catches
    ValueError (non-compliant filename) and converts it to a JSON error.

    Calls bump_version() and prints the result as JSON.
    """
    # Need at least: argv[0]=script, [1]=bump, [2]=filename, [3]=level
    if len(sys.argv) < 4:
        _err("Usage: naming.py bump <filename> <major|minor|patch>")

    filename = sys.argv[2]
    level    = sys.argv[3]

    # Pre-validate level — stricter check here so the error message is
    # clear before we even attempt to parse the filename.
    if level not in ("major", "minor", "patch"):
        _err(f"Invalid bump level: '{level}'.  Use major/minor/patch.")

    try:
        print(json.dumps(bump_version(filename, level), ensure_ascii=False))
    except ValueError as e:
        # Only possible cause: filename did not match the canonical regex.
        _err(str(e))


def _cmd_archive() -> None:
    """CLI handler: ``naming.py archive <file_path>``.

    Validates that the source path exists on disk before calling
    archive_old_version().  Prints the result (archived / to paths) as JSON.

    Calls archive_old_version() and prints the result as JSON.
    """
    # Need at least: argv[0]=script, [1]=archive, [2]=file_path
    if len(sys.argv) < 3:
        _err("Usage: naming.py archive <file_path>")

    src = Path(sys.argv[2])

    # Pre-check — archive_old_version also checks, but an early check gives
    # a cleaner error message at the CLI level.
    if not src.exists():
        _err(f"File not found: {src}")

    dest = archive_old_version(src)
    if dest:
        print(json.dumps(
            {"archived": str(src), "to": str(dest)},
            ensure_ascii=False,
        ))
    else:
        # Should not normally happen since we pre-checked existence,
        # but guard against TOCTOU or permission issues during rename.
        _err("Archive failed")


def main() -> None:
    """Entry point — dispatch to the correct sub-command.

    Uses a dispatch table (dict mapping command name → (usage, handler)).
    This is more maintainable than an if/elif chain — adding a new
    command only requires one new dict entry.

    On missing or unknown command, prints a JSON error with available
    commands and exits with code 1.
    """
    # Dispatch table: command → (usage_string, handler_function)
    cmds = {
        "generate": (
            "generate <title> <ext> --type <type> --author <author> [--date YYYYMMDD]",
            _cmd_generate,
        ),
        "bump": (
            "bump <filename> <major|minor|patch>",
            _cmd_bump,
        ),
        "archive": (
            "archive <file_path>",
            _cmd_archive,
        ),
    }

    # No command at all — show available commands.
    if len(sys.argv) < 2:
        _err(f"Usage: naming.py <{'|'.join(cmds)}> [args...]")

    cmd = sys.argv[1]
    if cmd in cmds:
        # Call the handler (cmds[cmd][1]) — the usage string (cmds[cmd][0])
        # is kept for reference / potential future --help output.
        cmds[cmd][1]()
    else:
        _err(f"Unknown command: '{cmd}'")


if __name__ == "__main__":
    main()
