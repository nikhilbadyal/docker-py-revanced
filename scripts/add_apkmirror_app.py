#!/usr/bin/env python3
r"""CLI to register a new APKMirror app in the repo.

This script automates the manual edits required when ReVanced adds support for a
new app that's available on APKMirror. It updates:
- src/downloader/sources.py: adds the APKMirror source mapping
- src/patches.py: maps package name -> app key
- README.md: appends the bullet link under the officially supported list

Usage examples:
  python scripts/add_apkmirror_app.py \
    --package com.facebook.katana \
    --name facebook \
    --apkmirror-path facebook-2/facebook

  python scripts/add_apkmirror_app.py \
    --package com.facebook.katana \
    --name facebook \
    --apkmirror-url https://www.apkmirror.com/apk/facebook-2/facebook/

Notes
-----
- APKMirror only. For other sources, extend the script accordingly.
- Idempotent: if entries already exist, it will skip updating that file.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import requests
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Collection

REPO_ROOT = Path(__file__).resolve().parents[1]
ORG_APP_PARTS = 2
APK_MIRROR_APP_EXISTS_URL = "https://www.apkmirror.com/wp-json/apkm/v1/app_exists/"
DEFAULT_USER_AGENT = os.getenv("APKMIRROR_USER_AGENT", "nikhil")
DEFAULT_BASIC_AUTH = os.getenv(
    "APKMIRROR_AUTH_BASIC",
    # base64("api-apkupdater:rm5rcfruUjKy04sMpyMPJXW8") as provided in the example
    "YXBpLWFwa3VwZGF0ZXI6cm01cmNmcnVVakt5MDRzTXB5TVBKWFc4",
)
DEFAULT_HTTP_TIMEOUT_SECS = 20
APP_NAME_PRIMARY_SEPARATOR = re.compile("\\s*(?::|\\|| - | \\N{EN DASH} | \\N{EM DASH} )\\s*")


@dataclass(frozen=True)
class APKMirrorApp:
    """APKMirror app metadata needed to register a ReVanced-supported package."""

    package_name: str
    org: str
    app: str
    display_name: str

    @property
    def url(self) -> str:
        """Return the canonical APKMirror app page URL used in README entries and PR bodies."""
        return f"https://www.apkmirror.com/apk/{self.org}/{self.app}/"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for registering an APKMirror app."""
    parser = argparse.ArgumentParser(description="Register a new APKMirror app")
    parser.add_argument("--package", required=True, help="Android package name, e.g., com.facebook.katana")
    parser.add_argument(
        "--name",
        help="Short app key/name used in configs; defaults to a stable key derived from APKMirror metadata",
    )

    apkmirror = parser.add_mutually_exclusive_group(required=False)
    apkmirror.add_argument(
        "--apkmirror-path",
        help="APKMirror path '<org>/<app>' without leading /apk/, e.g., 'facebook-2/facebook'",
    )
    apkmirror.add_argument(
        "--apkmirror-url",
        help="Full APKMirror app URL, e.g., https://www.apkmirror.com/apk/facebook-2/facebook/",
    )

    parser.add_argument(
        "--apkmirror-auth",
        default=DEFAULT_BASIC_AUTH,
        help="Base64 for Basic Authorization header to APKMirror API (env: APKMIRROR_AUTH_BASIC)",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="User-Agent value for APKMirror API (env: APKMIRROR_USER_AGENT)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned changes without writing files",
    )

    return parser.parse_args()


def extract_apkmirror_path(url_or_path: str) -> tuple[str, str]:
    """Return (org, app) from a full URL or 'org/app' path.

    Accepted examples:
      - facebook-2/facebook
      - https://www.apkmirror.com/apk/facebook-2/facebook/
      - https://www.apkmirror.com/apk/facebook-2/facebook
    """
    raw = url_or_path.strip()
    if raw.startswith("http"):
        # Keep only the path after '/apk/'
        m = re.search(r"/apk/([^/?#]+)/([^/?#]+)/?", raw)
        if not m:
            msg = "Unable to parse APKMirror URL. Expected .../apk/<org>/<app>/."
            raise ValueError(
                msg,
            )
        org, app = m.group(1), m.group(2)
    else:
        # org/app
        parts = raw.strip("/").split("/")
        if len(parts) != ORG_APP_PARTS:
            msg = "--apkmirror-path must be '<org>/<app>'"
            raise ValueError(msg)
        org, app = parts
    return org, app


def slugify_app_key(value: str) -> str:
    """Convert human app text into the lowercase config-key shape used by this repository."""
    # Treat plus signs as a word because app names such as Disney+ would otherwise lose meaningful identity.
    value = value.replace("+", " plus ")
    # Normalize accents before stripping punctuation so generated keys stay ASCII and shell-friendly.
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    # Treat every punctuation run as a separator because app names often contain spaces, colons, and trademark marks.
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def derive_app_key(metadata: APKMirrorApp, reserved_keys: Collection[str] = ()) -> str:
    """Derive a stable app key from APKMirror metadata, avoiding keys already used by supported apps."""
    # APKMirror titles often include marketing suffixes after a separator, so prefer the recognizable primary name.
    primary_name = APP_NAME_PRIMARY_SEPARATOR.split(metadata.display_name, maxsplit=1)[0].strip()
    app_key = slugify_app_key(primary_name) or slugify_app_key(metadata.app)
    reserved = set(reserved_keys)
    if app_key not in reserved:
        return app_key

    # If the friendly name collides with an existing app, append the package tail to keep the generated PR isolated.
    package_suffix = slugify_app_key(metadata.package_name.rsplit(".", maxsplit=1)[-1])
    collision_key = f"{app_key}-{package_suffix}" if package_suffix else f"{app_key}-app"
    counter = 2
    while collision_key in reserved:
        collision_key = f"{app_key}-{package_suffix or 'app'}-{counter}"
        counter += 1
    return collision_key


def _select_api_item(data: dict[str, object], package_name: str) -> dict[str, object]:
    """Select the API item for the requested package and reject APKMirror misses early."""
    items = data.get("data") or []
    if not isinstance(items, list) or not items:
        msg = f"No data returned from APKMirror for {package_name}"
        raise RuntimeError(msg)

    # APKMirror preserves request order today, but matching by `pname` avoids trusting that undocumented behavior.
    item = next(
        (candidate for candidate in items if isinstance(candidate, dict) and candidate.get("pname") == package_name),
        None,
    )
    if item is None and isinstance(items[0], dict) and "pname" not in items[0]:
        item = items[0]
    if item is None or not item.get("exists"):
        msg = f"APKMirror does not have an app for {package_name}"
        raise RuntimeError(msg)
    return item


def _object_dict(value: object) -> dict[str, object]:
    """Return JSON object values as typed dictionaries and treat other JSON values as absent."""
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return {}


def _metadata_from_api_response(package_name: str, data: dict[str, object]) -> APKMirrorApp:
    """Parse the small subset of APKMirror API metadata needed for repo registration."""
    item = _select_api_item(data, package_name)
    app_data = _object_dict(item.get("app"))
    release_data = _object_dict(item.get("release"))
    app_link = app_data.get("link") or release_data.get("link")
    if not isinstance(app_link, str):
        msg = "APKMirror response missing app/release link"
        raise TypeError(msg)

    # App and release links both include `/apk/<org>/<app>/`; the release path may continue after those segments.
    m = re.search(r"/apk/([^/]+)/([^/]+)(?:/|$)", app_link)
    if not m:
        msg = "Unable to parse org/app from APKMirror response link"
        raise RuntimeError(msg)

    raw_display_name = app_data.get("name")
    display_name = html.unescape(str(raw_display_name or m.group(2))).strip()
    return APKMirrorApp(package_name=package_name, org=m.group(1), app=m.group(2), display_name=display_name)


def discover_apkmirror_app_via_api(package_name: str, auth_b64: str, user_agent: str) -> APKMirrorApp:
    """Query APKMirror app_exists API to discover the app metadata for a package.

    Tries `app.link` first, then falls back to `release.link`.
    Returns APKMirror metadata used by the source, patch, and README updates.
    """
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "User-Agent": user_agent,
        "Content-Type": "application/json",
    }
    payload = {"pnames": [package_name]}
    resp = requests.post(
        APK_MIRROR_APP_EXISTS_URL,
        headers=headers,
        json=payload,
        timeout=DEFAULT_HTTP_TIMEOUT_SECS,
    )
    if resp.status_code != 200:  # noqa: PLR2004
        msg = f"APKMirror app_exists API error: HTTP {resp.status_code}"
        raise RuntimeError(msg)
    data = resp.json()
    return _metadata_from_api_response(package_name, data)


def read_text(path: Path) -> str:
    """Read text from a file using UTF-8 encoding."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write text to a file using UTF-8 encoding."""
    path.write_text(content, encoding="utf-8")


def _process_char_in_dict_parsing(
    ch: str,
    depth: int,
    in_str: str | None,
    *,
    esc: bool,
) -> tuple[int, str | None, bool]:
    """Process a single character during dictionary brace parsing.

    Returns: (new_depth, new_in_str, new_esc)
    """
    if in_str:
        if esc:
            return depth, in_str, False
        if ch == "\\":
            return depth, in_str, True
        if ch == in_str:
            return depth, None, False
    elif ch in ('"', "'"):
        return depth, ch, False
    elif ch == "{":
        return depth + 1, in_str, False
    elif ch == "}":
        return depth - 1, in_str, False

    return depth, in_str, esc


@dataclass
class DictInsertParams:
    """Parameters for dictionary key-value insertion."""

    content: str
    brace_start: int
    brace_end: int
    body: str
    indent: str
    key: str
    value_code: str


def _find_dict_braces(content: str, open_match: re.Match[str]) -> tuple[int, int]:
    """Find the start and end indices of dictionary braces.

    Returns: (brace_start, brace_end)
    """
    # Find the '{' start index
    brace_start = content.find("{", open_match.start())
    if brace_start == -1:
        msg = "Malformed dictionary start: missing '{'"
        raise RuntimeError(msg)

    # Walk to matching '}' while handling strings and escape sequences
    i = brace_start
    depth = 0
    in_str: str | None = None
    esc = False

    while i < len(content):
        ch = content[i]
        depth, in_str, esc = _process_char_in_dict_parsing(ch, depth, in_str, esc=esc)

        if ch == "}" and depth == 0:
            return brace_start, i

        i += 1

    # If we reach here, we didn't find the matching closing brace
    msg = "Malformed dictionary: missing closing '}'"
    raise RuntimeError(msg)


def _calculate_indentation(content: str, brace_start: int, body: str) -> str:
    """Calculate the proper indentation for a new dictionary entry."""
    # Look for first item indentation
    item_match = re.search(r"^(?P<indent>[ \t]+)\"[^\n]+\"\s*:\s*", body, re.MULTILINE)
    if item_match:
        return item_match.group("indent")

    # Fallback: compute from dictionary line indentation
    line_start = content.rfind("\n", 0, brace_start) + 1
    base_indent = content[line_start:brace_start].rsplit("\n", maxsplit=1)[-1]

    # Count leading spaces/tabs of the line
    m_leading = re.match(r"^[ \t]*", base_indent)
    if not m_leading:
        msg = "Could not determine indentation for dictionary body"
        raise RuntimeError(msg)
    leading = m_leading.group(0)
    return leading + " " * 4


def _key_exists_in_dict(body: str, key: str) -> bool:
    """Check if a key already exists in the dictionary body."""
    key_re = re.compile(rf"^[ \t]*\"{re.escape(key)}\"\s*:\s*", re.MULTILINE)
    return bool(key_re.search(body))


def _split_body_and_closing_indent(body: str) -> tuple[str, str]:
    """Split dictionary body content from indentation that belongs to the closing brace."""
    # The parser stops at the closing brace, so any spaces before `}` are still inside `body`.
    closing_indent_match = re.search(r"\n(?P<indent>[ \t]*)\Z", body)
    if not closing_indent_match:
        return body, ""

    # Removing the final line break prevents the inserted item from being separated by a blank line.
    return body[: closing_indent_match.start()], closing_indent_match.group("indent")


def _insert_kv_entry(params: DictInsertParams) -> str:
    """Insert the key-value entry into the dictionary."""
    body, closing_indent = _split_body_and_closing_indent(params.body)
    new_entry = f'\n{params.indent}"{params.key}": {params.value_code},'
    # Reattach the closing indentation after the inserted entry so class-level dicts keep their closing brace aligned.
    new_body = body + new_entry + "\n" + closing_indent
    return params.content[: params.brace_start + 1] + new_body + params.content[params.brace_end :]


def insert_kv_into_dict(
    content: str,
    dict_var_pattern: str,
    key: str,
    value_code: str,
) -> tuple[str, bool]:
    r"""Insert a key/value into a Python dict literal for a variable.

    - dict_var_pattern: regex to match the variable assignment line that opens the dict
      e.g., r"revanced_package_names[\s\S]*?=\s*\{"
    - key: dictionary key to insert (without quotes)
    - value_code: full code for the value expression (already quoted/f-string as needed)

    Returns: (new_content, changed)
    """
    # Find dict opening
    open_match = re.search(dict_var_pattern, content)
    if not open_match:
        msg = "Could not locate dictionary with given pattern"
        raise RuntimeError(msg)

    # Find dictionary braces
    brace_start, brace_end = _find_dict_braces(content, open_match)

    # Get dictionary body
    body = content[brace_start + 1 : brace_end]

    # Check if key already exists
    if _key_exists_in_dict(body, key):
        return content, False

    # Calculate indentation
    indent = _calculate_indentation(content, brace_start, body)

    # Insert the new entry
    params = DictInsertParams(content, brace_start, brace_end, body, indent, key, value_code)
    new_content = _insert_kv_entry(params)
    return new_content, True


def update_sources_py(app_key: str, org: str, app: str, *, dry_run: bool) -> bool:
    """Update `src/downloader/sources.py` with the APKMirror mapping.

    Returns True if a change was made.
    """
    path = REPO_ROOT / "src" / "downloader" / "sources.py"
    content = read_text(path)
    value_code = f'f"{ '{' }APK_MIRROR_BASE_APK_URL{ '}' }/{org}/{app}/"'
    pattern = r"apk_sources\s*=\s*\{"
    new_content, changed = insert_kv_into_dict(content, pattern, app_key, value_code)
    if changed and not dry_run:
        write_text(path, new_content)
    return changed


def update_patches_py(package_name: str, app_key: str, *, dry_run: bool) -> bool:
    """Update `src/patches.py` with package -> app key mapping.

    Returns True if a change was made.
    """
    path = REPO_ROOT / "src" / "patches.py"
    content = read_text(path)
    value_code = f'"{app_key}"'
    # Match the dict assignment, accommodating type annotations
    pattern = r"revanced_package_names[\s\S]*?=\s*\{"
    new_content, changed = insert_kv_into_dict(content, pattern, package_name, value_code)
    if changed and not dry_run:
        write_text(path, new_content)
    return changed


def update_readme_md(app_key: str, org: str, app: str, *, dry_run: bool) -> bool:
    """Insert the README bullet link for the new app.

    Returns True if a change was made.
    """
    path = REPO_ROOT / "README.md"
    content = read_text(path)
    bullet = f"    - [{app_key}](https://www.apkmirror.com/apk/{org}/{app}/)"

    # Check if already present (exact label match, beginning of bullet)
    exists_pattern = re.compile(r"^\s*-\s*\[" + re.escape(app_key) + r"\]\(", flags=re.MULTILINE)
    if exists_pattern.search(content):
        return False

    # Locate the supported list block
    # Insert before the note that ends the list
    note = re.search(r"^\s*<br>`\*\*` - You can also patch any other app", content, re.MULTILINE)
    if note:
        insert_pos = note.start()
        new_content = content[:insert_pos] + bullet + "\n" + content[insert_pos:]
    else:
        # Fallback: append at end
        new_content = content.rstrip("\n") + "\n" + bullet + "\n"

    if not dry_run:
        write_text(path, new_content)
    return True


def main() -> None:
    """Entry point: parse args, perform updates, and report results."""
    args = parse_args()

    if args.apkmirror_path or args.apkmirror_url:
        org, app = extract_apkmirror_path(args.apkmirror_path or args.apkmirror_url)
        metadata = APKMirrorApp(package_name=args.package, org=org, app=app, display_name=app)
    else:
        metadata = discover_apkmirror_app_via_api(args.package, args.apkmirror_auth, args.user_agent)

    app_key = args.name or derive_app_key(metadata)

    changed_any = False
    changed_sources = update_sources_py(app_key, metadata.org, metadata.app, dry_run=args.dry_run)
    changed_any = changed_any or changed_sources

    changed_patches = update_patches_py(args.package, app_key, dry_run=args.dry_run)
    changed_any = changed_any or changed_patches

    changed_readme = update_readme_md(app_key, metadata.org, metadata.app, dry_run=args.dry_run)
    changed_any = changed_any or changed_readme

    if not changed_any:
        logger.info("No changes needed; app may already be registered.")


if __name__ == "__main__":
    main()
